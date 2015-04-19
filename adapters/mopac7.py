# -*- coding:utf-8 mode:python; tab-width:4; indent-tabs-mode:nil; py-indent-offset:4 -*-

import hashlib
import os
import uuid
import cpinterface

class Mopac7Job(cpinterface.Job):
    def __init__(self, *args, **kw):
        super(Mopac7Job, self).__init__(*args, **kw)
        self.backend = "mopac7"

    def extract_last_energy(self, data, options={}):
        """Get last energy message from log file and store it as energy.

        @param data: log file contents
        @type data : str
        @param options: ignored
        @type options : dict
        """

        electronic_energy = None
        core_repulsion = None
        
        for line in data.split("\n"):
            if "ELECTRONIC ENERGY" in line:
                electronic_energy = self.n_number_from_line(line, 0, 1)

            elif "CORE-CORE REPULSION" in line:
                core_repulsion = self.n_number_from_line(line, 0, 1)

        #total energy is the sum of electronic energy and core repulsion
        if electronic_energy is not None and core_repulsion is not None:
            self.energy = self.ev_to_au(electronic_energy + core_repulsion)
            self.log("NOTE: energies from semiempirical methods are not directly comparable to ab initio energies")

        else:
            self.log("Unable to find energy. Electronic energy: {0} Core-core repulsion: {1}".format(electronic_energy, core_repulsion))

    def extract_heat_of_formation(self, data, options={}):
        """Get heat of formation from log file and store it
        as heat_of_formation.

        @param data: log file contents
        @type data : str
        @param options: ignored
        @type options : ignored
        """

        for line in data.split("\n"):
            if "HEAT OF FORMATION" in line:
                hof = self.n_number_from_line(line, 0, 1)
                self.heat_of_formation = self.kcalm_to_au(hof)
        
    def run_local(self, options={}):
        """Run MOPAC7 on the local host using the run_mopac7 script.

        @param options: ignored
        @type options : dict
        """
        
        workdir = self.backend + "-" + str(uuid.uuid1()).replace('-', '')[:16]
        path = "/tmp/{0}/".format(workdir)
        os.makedirs(path)

        deck_hash = hashlib.sha1(self.deck).hexdigest()[:10]
        dat_file = "{0}.dat".format(deck_hash)
        abs_file = path + dat_file
        with open(abs_file, "w") as deckfile:
            deckfile.write(self.deck)

        #N.B.: run_mopac7 does not like long paths!
        cmd = "run_mopac7 {0}".format(abs_file.split(".dat")[0])
        
        stdout, returncode = self.execute(cmd)
        self.stdout = stdout
        if "DUE TO PROGRAM BUG" in stdout:
            self.runstate = "error"
            return

        log_file = abs_file.replace(".dat", ".log")
        with open(log_file, "r") as lfile:
            self.logdata = lfile.read()
            self.extract_last_energy(self.logdata)
            self.extract_heat_of_formation(self.logdata)

        self.runstate = "complete"

class Mopac7(cpinterface.MolecularCalculator):
    def __init__(self, *args, **kw):
        super(Mopac7, self).__init__(*args, **kw)
        
        self.methods = ["semiempirical:am1", "semiempirical:pm3",
                        "semiempirical:mindo/3", "semiempirical:mndo"]
        self.coordinate_choices = ["cartesian", "zmatrix"]
        self.references = ["RHF", "UHF"]

    def check_element_support(self, system, method):
        """Check that the chosen semiempirical method is parameterized for
        all the elements in the system. Supported elements are taken from
        section 3.5 of the Mopac 7 manual. Unsupported elements will raise
        an exception.

        Note that MINDO/3 is supported only for certain *pairs* of elements,
        and this check may let bad pairs slip through because it is not
        pair-aware.

        @param system: molecular system
        @type system : geoprep.System
        @param method: name of method
        @type method : str
        @return: elements from system
        """
        
        emap = {"semiempirical:mndo" : ["H", "Li", "B", "C", "N", "O", "F",
                                        "Al", "Si", "P", "S", "Cl", "Zn",
                                        "Ge", "Br", "Sn", "I", "Hg", "Pb"],
                "semiempirical:am1" : ["H", "B", "C", "N", "O", "F", "Al",
                                       "Si", "P", "S", "Cl", "Zn", "Ge", "Br",
                                       "Sn", "I", "Hg"],
                "semiempirical:pm3" : ["H", "Be", "C", "N", "O", "F", "Mg",
                                       "Al", "Si", "P", "S", "Cl", "Zn", "Ga",
                                       "Ge", "As", "Se", "Br", "Cd", "In",
                                       "Sn", "Sb", "Te", "I", "Hg", "Tl", "Pb",
                                       "Bi"],
                "semiempirical:mindo/3" : ["H", "B", "C", "N", "O", "F", "Si",
                                           "P", "S", "Cl"]}
        
        elements = system.elements
        allowed = emap[method]
        for e in elements:
            if e not in allowed:
                raise ValueError("Element {0} not parameterized for {1}".format(repr(e), repr(method)))

        return elements

    def check_coordinates(self, coordinate_choice):
        if coordinate_choice in self.coordinate_choices:
            return coordinate_choice

        else:
            raise ValueError("Unrecognized coordinates option {0}".format(repr(coordinate_choice)))

    
    def create_geometry(self, system, options={}):
        """Create input geometry for a subsequent calculation.

        options:
         coordinates: "cartesian" or "zmatrix"

        @param system: molecular system data to convert to input geometry
        @type system : geoprep.System
        @param options: select coordinate system
        @type options : dict
        @return: a Mopac7 input with geometry specifications
        @rtype : str
        """

        defaults = {"coordinates" : "cartesian"}
        options = dict(defaults.items() + options.items())
        
        coord_choice = self.check_coordinates(options.get("coordinates"))

        if coord_choice == "cartesian":
            geometry = system.write("mopcrt")

        elif coord_choice == "zmatrix":
            geometry = system.write("mopin")

        return geometry

    def make_energy_job(self, system, method, options={}):
        """Create an input specification for a single point energy calculation.

        @param system: molecular system for energy calculation
        @type system : geoprep.System
        @param method: calculation method
        @type method : str
        @param options: additional keyword based control options
        @type options : dict
        @return: a Mopac7 single point energy calculation job
        @rtype : cpinterface.Job
        """

        if method.startswith("semiempirical"):
            return self.make_semiempirical_job(system, method, "ENERGY",
                                               options=options)
        else:
            raise ValueError("Mopac 7 does not support {0}".format(method))

    def make_semiempirical_job(self, system, method, runtyp,
                               options={}):
        """Create a semiempirical input specification for a calculation.
        Mopac7 supports MNDO, MINDO/3, AM1, and PM3 methods.

        See Chapter 2 of the Mopac 7 manual for keyword details.

        @param system: molecular system for calculation
        @type system : geoprep.System
        @param method: a semiempirical calculation method
        @type method : str
        @param options: additional keyword based control options
        @type options : dict
        @return: a Mopac7 semiempirical job
        @rtype : Job
        """

        defaults = {"reference" : "rhf", "gnorm" : 0.0001, "precise" : True,
                    "let" : True, "scf_iterations" : 999}
        options = dict(defaults.items() + options.items())

        self.check_method(method)
        self.check_element_support(system, method)

        deck = self.create_geometry(system, options=options)
        semethod = method.split("semiempirical:")[-1].upper()        

        #MNDO is default method in Mopac7, so no keyword provided
        mmap = {"MNDO" : "" , "AM1" : "AM1",
                "MINDO/3" : "MINDO3", "PM3" : "PM3"}

        #RHF is default electronic reference in Mopac7, so no keyword provided
        rmap = {"RHF" : "", "UHF" : "UHF"}

        controls = []

        if system.spin > 6:
            raise ValueError("Spin of {0} too large: Mopac7 only works up to sextet".format(system.spin))

        else:
            spin_map = {1 : "SINGLET", 2 : "DOUBLET", 3 : "TRIPLET",
                        4 : "QUARTET", 5 : "QUINTET", 6 : "SEXTET"}
            spin_name = spin_map[system.spin]


        reference = rmap[options["reference"].upper()]
        self.check_electronic_reference(reference or options["reference"].upper())
        if system.spin > 1 and reference != "UHF":
            self.log("Forcing UHF for multiplicity {0}".format(system.spin))
            reference = "UHF"
            
        controls.append(reference)
        controls.append(spin_name)
        controls.append(mmap[semethod])

        #Default is to optimize geometry; "1SCF" gives a single-point energy
        if runtyp == "ENERGY":
            controls.append("1SCF")

        if options.get("gnorm"):
            controls.append("GNORM={0:.5f}".format(options.get("gnorm")))

        if options.get("precise"):
            controls.append("PRECISE")

        if options.get("let"):
            controls.append("LET")

        if options.get("scf_iterations"):
            controls.append("ITRY={0}".format(options.get("scf_iterations")))

        if system.charge != 0:
            controls.append("CHARGE={0}".format(system.charge))

        keywords = " ".join([c for c in controls if c])
        deck = deck.replace("PUT KEYWORDS HERE", keywords)

        job = Mopac7Job(deck=deck, system=system)

        return job
