import numpy as np
import re

import dpdata.vasp_deltaspin.outcar
import dpdata.vasp_deltaspin.poscar
from dpdata.format import Format
from dpdata.utils import uniq_atom_names


@Format.register("vasp_deltaspin/poscar")
@Format.register("vasp_deltaspin/contcar")
class VASPPoscarFormat(Format):
    @Format.post("rot_lower_triangular")
    def from_system(self, file_name, **kwargs):
        with open(file_name) as fp:
            lines = [line.rstrip("\n") for line in fp]
        with open(file_name[:-6] + 'INCAR') as fp:
            lines_incar = [line.rstrip("\n") for line in fp]
        data = dpdata.vasp_deltaspin.poscar.to_system_data(lines, lines_incar)
        data = uniq_atom_names(data)
        return data

    def to_system(self, data, file_name, frame_idx=0, **kwargs):
        """Dump the system in vasp POSCAR format.

        Parameters
        ----------
        data : dict
            The system data
        file_name : str
            The output file name
        frame_idx : int
            The index of the frame to dump
        **kwargs : dict
            other parameters
        """
        w_str, m_str = VASPStringFormat().to_system(data, frame_idx=frame_idx)
        with open(file_name, "w") as fp:
            fp.write(w_str)

        with open(file_name[:-6] + 'INCAR') as fp:
            tmp_incar = fp.read()
        res_incar = re.sub(r'MAGMOM[\s\S]*?\n\nM_CONST[\s\S]*?\n\n', m_str, tmp_incar, re.S)
        with open(file_name[:-6] + 'INCAR', 'w') as fp:
            fp.write(res_incar)


@Format.register("vasp/string")
class VASPStringFormat(Format):
    def to_system(self, data, frame_idx=0, **kwargs):
        """Dump the system in vasp POSCAR format string.

        Parameters
        ----------
        data : dict
            The system data
        frame_idx : int
            The index of the frame to dump
        **kwargs : dict
            other parameters
        """
        assert frame_idx < len(data["coords"])
        return dpdata.vasp_deltaspin.poscar.from_system_data(data, frame_idx)


# rotate the system to lammps convention
@Format.register("vasp_deltaspin/outcar")
class VASPOutcarFormat(Format):
    @Format.post("rot_lower_triangular")
    def from_labeled_system(
        self, file_name, begin=0, step=1, convergence_check=True, **kwargs
    ):
        data = {}
        ml = kwargs.get("ml", False)
        (
            data["atom_names"],
            data["atom_numbs"],
            data["atom_types"],
            data["cells"],
            data["coords"],
            data['spins'],
            data["energies"],
            data["forces"],
            data['mag_forces'],
            tmp_virial,
        ) = dpdata.vasp_deltaspin.outcar.get_frames(
            file_name,
            begin=begin,
            step=step,
            ml=ml,
            convergence_check=convergence_check,
        )
        if tmp_virial is not None:
            data["virials"] = tmp_virial
        # scale virial to the unit of eV
        if "virials" in data:
            v_pref = 1 * 1e3 / 1.602176621e6
            for ii in range(data["cells"].shape[0]):
                vol = np.linalg.det(np.reshape(data["cells"][ii], [3, 3]))
                data["virials"][ii] *= v_pref * vol
        data = uniq_atom_names(data)
        return data

