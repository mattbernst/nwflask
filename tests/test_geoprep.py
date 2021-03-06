# -*- coding:utf-8 mode:python; tab-width:4; indent-tabs-mode:nil; py-indent-offset:4 -*-
##

"""
    test_geoprep
    ~~~~~~~~~~~~~~

    Test backend-independent functionality: fragment, system, basis name
    assignment...
"""

import copy
import cStringIO as StringIO
import random
import sys
import unittest
import geoprep
from tests.common_testcode import runSuite

from cinfony import pybel

class GTestCase(unittest.TestCase):

    def setUp(self):
        self.G = geoprep.Geotool()

    def test_spin_assignment(self):
        #create triplet oxygen
        oxygen = self.G.make_fragment("[O][O]")
        self.assertEqual(3, oxygen.spin)
        
        #make it singlet
        oxygen.spin = 1
        self.assertEqual(1, oxygen.spin)

    def test_nelec(self):
        #count the number of electrons

        methyl_radical = self.G.make_fragment("[CH3]")
        methylium = self.G.make_fragment("[CH3+]")
        carbanide = self.G.make_fragment("[CH3-]")

        self.assertEqual(9, methyl_radical.nelec)
        self.assertEqual(methyl_radical.nelec + 1, carbanide.nelec)
        self.assertEqual(methyl_radical.nelec - 1, methylium.nelec)

    def test_spin_guess(self):
        #test spin multiplicity as guessed by underlying OpenBabel code
        methane = self.G.make_fragment("[CH4]")
        methyl_radical = self.G.make_fragment("[CH3]")
        methylene_diradical = self.G.make_fragment("[CH2]")

        self.assertEqual(1, methane.spin)
        self.assertEqual(2, methyl_radical.spin)

        #This could be singlet or triplet. OpenBabel assumes triplet. No way
        #to specify ambiguous multiplicity in standard SMILES.
        self.assertEqual(3, methylene_diradical.spin)

    def test_system_nelec(self):
        #count all electrons (sum of per-fragment nelec)
        methane = self.G.make_fragment("C")
        water = self.G.make_fragment("O")
        s = geoprep.System([methane, water])

        self.assertEqual(methane.nelec + water.nelec, s.nelec)

    def test_system_spin_guess(self):
        #spin multiplicity is inherited from the first fragment in the system
        #unless explicitly set
        methylene_diradical = self.G.make_fragment("[CH2]")
        water = self.G.make_fragment("O")
        s = geoprep.System([methylene_diradical, water])

        self.assertEqual(methylene_diradical.spin, s.spin)
        s.spin = 1
        self.assertEqual(1, s.spin)
        
    def test_system_charge(self):
        #system charge is the sum of fragment charges

        azanide = self.G.make_fragment("[NH2-]")
        methylium = self.G.make_fragment("[CH3+]")
        s = geoprep.System([azanide, methylium, azanide])

        self.assertEqual(-1, s.charge)

    def test_system_elements(self):
        #unique elements in system, ordered by ascending atomic number
        
        halothane = self.G.make_fragment("C(C(F)(F)F)(Cl)Br")
        cysteine = self.G.make_fragment("C([C@@H](C(=O)O)N)S")
        s = geoprep.System([halothane, cysteine])
        expected = ["H", "C", "N", "O", "F", "S", "Cl", "Br"]
        
        self.assertEqual(expected, s.elements)

    def test_system_title(self):
        #system title can be set explicitly or inherits from first fragment
        name = "azanide"
        azanide = self.G.make_fragment("[NH2-]")
        azanide.title = name
        methylium = self.G.make_fragment("[CH3+]")
        s = geoprep.System([azanide, methylium, azanide])

        self.assertEqual(name, s.title)

        name2 = "amide ion"
        s.title = name2
        self.assertEqual(name2, s.title)

    def test_hydrogen_selectors(self):
        triethylamine = self.G.make_fragment("CCN(CC)CC")
        ethyl = "[C][C]"

        #heavy atoms (carbon) of ethyl groups alone
        e1 = [[0, 1], [3, 4], [5, 6]]
        #hydrogen atoms attached to ethyl groups, alone
        e2 = [[7, 8, 9, 10, 11], [12, 13, 14, 15, 16], [17, 18, 19, 20, 21]]
        #ethyl groups each including hydrogens
        e3 = [[0, 1, 7, 8, 9, 10, 11], [3, 4, 12, 13, 14, 15, 16],
              [5, 6, 17, 18, 19, 20, 21]]
        
        m1 = triethylamine.select(ethyl, hydrogen="exclude", flatten=False)
        m2 = triethylamine.select(ethyl, hydrogen="only", flatten=False)
        m3 = triethylamine.select(ethyl, hydrogen="include", flatten=False)

        self.assertEqual(e1, m1)
        self.assertEqual(e2, m2)
        self.assertEqual(e3, m3)

    def test_select_hydrogens(self):
        triethylamine = self.G.make_fragment("CCN(CC)CC")
        ethyl = "[C][C]"
        s = pybel.Smarts(ethyl)
        
        selected = s.findall(triethylamine.molecule)
        expectations = [[7, 8, 9, 10, 11],
                        [12, 13, 14, 15, 16],
                        [17, 18, 19, 20, 21]]

        for k, ethyl in enumerate(selected):
            #cinfony.pybel uses 0-based indexing while the lower level pybel
            #uses 1-based indexing, so subtract 1 from each index in match
            e = [s - 1 for s in ethyl]
            hydrogens = triethylamine.select_hydrogens(e)
            self.assertEqual(expectations[k], hydrogens)
            for h in hydrogens:
                self.assertEqual(1, triethylamine.atoms[h].atomicnum)

    def test_set_basis_name(self):
        #test basis set assignment: assign one basis set for all atoms and
        #then another for ethyl carbons
        expected = ["cc-pVTZ", "cc-pVTZ", "cc-pVDZ", "cc-pVTZ", "cc-pVTZ",
                    "cc-pVTZ", "cc-pVTZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ", "cc-pVDZ"]
        
        triethylamine = self.G.make_fragment("CCN(CC)CC")
        ethyl_carbons = triethylamine.select("[C][C]", hydrogen="exclude")

        triethylamine.set_basis_name("cc-pVDZ")
        triethylamine.set_basis_name("cc-pVTZ", selection=ethyl_carbons)
        self.assertEqual(expected, triethylamine.atom_properties["basis_name"])

    def test_system_atom_properties_basic(self):
        #test atom property retrieval across all fragments in a system, using
        #basis set names as properties
        expected = ["cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ",
                    "cc-pVQZ", "cc-pVQZ", "cc-pVQZ", "cc-pVQZ", "cc-pVQZ",
                    "cc-pVQZ", "cc-pVQZ", "cc-pVQZ",
                    None, None, None, None, None]
        
        propane = self.G.make_fragment("CCC")
        propane.set_basis_name("cc-pVDZ")
        ethane = self.G.make_fragment("CC")
        ethane.set_basis_name("cc-pVQZ")
        methane = self.G.make_fragment("C")

        s = geoprep.System([propane, ethane, methane])
        props = s.atom_properties("basis_name")
        self.assertEqual(expected, props)

    def test_system_atom_properties_mixed(self):
        #test atom property retrieval with a mixture of system-level
        #properties and fragment-level properties
        expected = ["cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ", "cc-pVDZ",
                    "cc-pVDZ",
                    "cc-pVQZ", "cc-pVQZ", "cc-pVQZ", "cc-pVQZ", "cc-pVQZ",
                    "cc-pVQZ", "cc-pVQZ", "cc-pVTZ",
                    "cc-pVTZ", "cc-pVTZ", "cc-pVTZ", "cc-pVTZ", "cc-pVTZ"]
        
        propane = self.G.make_fragment("CCC")
        propane.set_basis_name("cc-pVDZ")
        ethane = self.G.make_fragment("CC")
        ethane.set_basis_name("cc-pVQZ")
        methane = self.G.make_fragment("C")

        s = geoprep.System([propane, ethane, methane])

        #overlay a different basis for the last 6 atoms, which will take
        #precedence over fragment-level settings
        s_props = [None] * len(s.atoms)
        s_indexes = range(len(s.atoms))[-6:]
        s.set_properties("basis_name", s_indexes, ["cc-pVTZ"] * 6)
        props = s.atom_properties("basis_name")
        self.assertEqual(expected, props)

    def test_system_select(self):
        #test selector operating across all fragments in system

        pg = self.G.make_fragment("CC(O)CO")
        ethanol = self.G.make_fragment("CCO")
        hydroxyl = "[OX2H]"

        s = geoprep.System([pg, ethanol])
        selected = s.select(hydroxyl)
        for k in selected:
            symbol = s.atom_properties("symbols")[k]
            self.assertTrue(symbol in "OH")

    def assertSameGeometry(self, f1, f2, max_rmsd):
        #test that two fragments have the same atoms and xyz coordinates match
        #to within max_rmsd
        rmsd = self.G.align(f1, f2)["rmsd"]
                        
        if rmsd > max_rmsd:
            msg = "Aligned fragment geometry RMSD {0} is greater than than {1}".format(aligned["rmsd"], max_rmsd)
            raise AssertionError(msg)

    def test_fragment_read_write(self):
        #test reading and writing with a variety of file formats

        methanol = self.G.make_fragment("CO")
        prefix = str(random.randint(10**10, 10**11))
        
        for fmt in ["pdb", "xyz", "sdf"]:
            name = "/tmp/{0}.{1}".format(prefix, fmt)
            methanol.write_fragment(name)
            read_fragment = self.G.read_fragment(name)
            self.assertSameGeometry(methanol, read_fragment, 0.001)

    def test_mcs_basic(self):
        #test maximum common substructure search across identical molecules

        methanol = self.G.make_fragment("CO")
        prefix = str(random.randint(10**10, 10**11))
        fragments = [methanol]
        
        for fmt in ["pdb", "xyz", "sdf"]:
            sio = StringIO.StringIO()
            #name = "/tmp/{0}.{1}".format(prefix, fmt)
            methanol.write_fragment(fmt=fmt, handle=sio)
            sio.seek(0)
            read_fragment = self.G.read_fragment(handle=sio, fmt=fmt)
            sio.close()
            fragments.append(read_fragment)

        expected = {"numAtoms" : 2, "numBonds" : 1, "smarts" : "[#6]-[#8]"}
        ss = self.G.mcs(fragments)
        for k in expected:
            v = expected[k]
            self.assertEqual(v, getattr(ss, k))

    def test_align_basic(self):
        #test easiest case for molecule alignment: molecules the very same
        
        methanol = self.G.make_fragment("CO")
        copied = copy.deepcopy(methanol)
        alignment = self.G.align(methanol, copied)
        self.assertTrue(alignment["rmsd"] < 10**-5)

    def test_align_hydrogens(self):
        #validate effects of including hydrogens in alignment and RMSD

        #hydrogens considered (default) leads to high RMSD for different
        #ethane conformations
        ethane1 = self.G.read_fragment("tests/data/ethane-staggered.xyz")
        ethane2 = self.G.read_fragment("tests/data/ethane-eclipsed.xyz")
        alignment = self.G.align(ethane1, ethane2)
        self.assertTrue(alignment["rmsd"] > 0.3)

        #otherwise RMSD is effectively zero for different ethane conformations
        alignment_heavy = self.G.align(ethane1, ethane2, includeH=False)
        self.assertTrue(alignment_heavy["rmsd"] < 0.0001)

    def xtest_align_scrambled(self):
        #test harder case for molecule alignment: different ordering of atoms
        #N.B.: Test currently disabled! OBAlign does not support differently
        #ordered molecules for match. Perhaps at some future date I can add
        #a cleanup stage first to give canonical ordering...
        
        methanol = self.G.make_fragment("CO")

        #create XYZ representation of data, shuffle atom order, and read it
        #back in as a new fragment
        xyz = methanol.write("xyz").strip()
        lines = xyz.split("\n")
        head = lines[:2][:]
        tail = lines[2:][:]
        random.shuffle(tail)
        rejoined = "\n".join(head + tail)
        sio = StringIO.StringIO(rejoined)
        sio.seek(0)
        scrambled = self.G.read_fragment(fmt="xyz", handle=sio)
        sio.close()

        alignment = self.G.align(methanol, scrambled, symmetry=False)
        self.assertTrue(alignment["rmsd"] < 10**-5)

    def test_align_unequal_geometry(self):
        #test molecule alignment: atom order is different, geometry slightly
        #different, rotation is different

        methanol1 = self.G.read_fragment("tests/data/methanol1.xyz")
        methanol2 = self.G.read_fragment("tests/data/methanol2.xyz")
        alignment = self.G.align(methanol1, methanol2)
        self.assertTrue(alignment["rmsd"] < 0.95)

    def test_geolist_to_fragment(self):
        #test creation of new fragment from geometry list: geometry lists
        #should match exactly across fragments

        methanol = self.G.read_fragment("tests/data/methanol1.xyz")
        fcopy = self.G.geolist_to_fragment(methanol.geometry_list)
        self.assertEqual(methanol.geometry_list, fcopy.geometry_list)

    def test_deepcopy_fragment(self):
        #validate that deep copying duplicates a fragment and leaves the
        #duplicate independent of the original

        methanol = self.G.make_fragment("CO")
        copied = copy.deepcopy(methanol)

        self.assertTrue(methanol == copied)
        self.assertFalse(methanol != copied)

        #add new atom properties to copy; original is unaffected
        copied.set_basis_name("cc-pVDZ")
        self.assertFalse(methanol == copied)
        self.assertTrue(methanol != copied)
        self.assertNotEqual(methanol.atom_properties, copied.atom_properties)

    def test_translate(self):
        #test fragment geometry translation
        tvec = [1.5, 0.0, 0.0]
        CO = self.G.make_fragment("[C-]#[O+]")
        g1 = CO.geometry_list
        CO.translate(tvec)
        g2 = CO.geometry_list

        for j in range(len(g1)):
            for k in (1, 2, 3):
                self.assertEqual(g1[j][k] + tvec[k - 1], g2[j][k])

def runTests():
    try:
        test_name = sys.argv[1]
        
    except IndexError:
        test_name = None

    if test_name:
        result = runSuite(GTestCase, name = test_name)

    else:
        result = runSuite(GTestCase)

    return result

if __name__ == "__main__":
    runTests()
