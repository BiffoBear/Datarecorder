from unittest import TestCase
import argparse
from commandline import addnode


class TestListNodesAndSensors(TestCase):

    def test_high_lite_existing_things(self):
        returned_result = addnode.high_lite_existing_things(thing=5, existing_things=[5])
        self.assertEqual(f'\x1b[1m05 \x1b[0m', returned_result)
        returned_result = addnode.high_lite_existing_things(thing=5, existing_things=[4])
        self.assertEqual(f'\x1b[90m05 \x1b[0m', returned_result)

    def test_print_existing_things_displays_correct_things(self):
        expected_result = '''\x1b[1mExisting Sensors[0m

[90m00 [0m[1m01 [0m[90m02 [0m[90m03 [0m[90m04 [0m[1m05 [0m[90m06 [0m[90m07 [0m[90m08 [0m[90m09 [0m[90m0a [0m[90m0b [0m[90m0c [0m[90m0d [0m[90m0e [0m[90m0f [0m
[90m10 [0m[90m11 [0m[90m12 [0m[90m13 [0m[90m14 [0m[90m15 [0m[90m16 [0m[90m17 [0m[90m18 [0m[90m19 [0m[90m1a [0m[90m1b [0m[90m1c [0m[90m1d [0m[90m1e [0m[90m1f [0m
[90m20 [0m[90m21 [0m[90m22 [0m[90m23 [0m[90m24 [0m[90m25 [0m[90m26 [0m[90m27 [0m[90m28 [0m[90m29 [0m[90m2a [0m[90m2b [0m[90m2c [0m[90m2d [0m[90m2e [0m[90m2f [0m
[90m30 [0m[90m31 [0m[90m32 [0m[90m33 [0m[90m34 [0m[90m35 [0m[90m36 [0m[90m37 [0m[90m38 [0m[90m39 [0m[90m3a [0m[90m3b [0m[90m3c [0m[90m3d [0m[90m3e [0m[90m3f [0m
[90m40 [0m[90m41 [0m[90m42 [0m[90m43 [0m[90m44 [0m[90m45 [0m[90m46 [0m[90m47 [0m[90m48 [0m[90m49 [0m[90m4a [0m[90m4b [0m[90m4c [0m[90m4d [0m[90m4e [0m[90m4f [0m
[90m50 [0m[90m51 [0m[90m52 [0m[90m53 [0m[90m54 [0m[90m55 [0m[90m56 [0m[90m57 [0m[90m58 [0m[90m59 [0m[90m5a [0m[90m5b [0m[90m5c [0m[90m5d [0m[90m5e [0m[90m5f [0m
[90m60 [0m[90m61 [0m[90m62 [0m[90m63 [0m[90m64 [0m[90m65 [0m[90m66 [0m[90m67 [0m[90m68 [0m[90m69 [0m[90m6a [0m[90m6b [0m[90m6c [0m[90m6d [0m[90m6e [0m[90m6f [0m
[90m70 [0m[90m71 [0m[90m72 [0m[90m73 [0m[90m74 [0m[90m75 [0m[90m76 [0m[90m77 [0m[90m78 [0m[90m79 [0m[90m7a [0m[90m7b [0m[90m7c [0m[90m7d [0m[90m7e [0m[90m7f [0m
[90m80 [0m[90m81 [0m[90m82 [0m[90m83 [0m[90m84 [0m[90m85 [0m[90m86 [0m[90m87 [0m[90m88 [0m[90m89 [0m[90m8a [0m[90m8b [0m[90m8c [0m[90m8d [0m[90m8e [0m[90m8f [0m
[90m90 [0m[90m91 [0m[90m92 [0m[90m93 [0m[90m94 [0m[90m95 [0m[90m96 [0m[90m97 [0m[90m98 [0m[90m99 [0m[90m9a [0m[90m9b [0m[90m9c [0m[90m9d [0m[90m9e [0m[90m9f [0m
[90ma0 [0m[90ma1 [0m[90ma2 [0m[90ma3 [0m[90ma4 [0m[90ma5 [0m[90ma6 [0m[90ma7 [0m[90ma8 [0m[90ma9 [0m[90maa [0m[90mab [0m[90mac [0m[90mad [0m[90mae [0m[90maf [0m
[90mb0 [0m[90mb1 [0m[90mb2 [0m[90mb3 [0m[90mb4 [0m[90mb5 [0m[90mb6 [0m[90mb7 [0m[90mb8 [0m[90mb9 [0m[90mba [0m[90mbb [0m[90mbc [0m[90mbd [0m[90mbe [0m[90mbf [0m
[90mc0 [0m[90mc1 [0m[90mc2 [0m[90mc3 [0m[90mc4 [0m[90mc5 [0m[90mc6 [0m[90mc7 [0m[90mc8 [0m[90mc9 [0m[90mca [0m[90mcb [0m[90mcc [0m[90mcd [0m[90mce [0m[90mcf [0m
[90md0 [0m[90md1 [0m[90md2 [0m[90md3 [0m[90md4 [0m[90md5 [0m[90md6 [0m[90md7 [0m[90md8 [0m[90md9 [0m[90mda [0m[90mdb [0m[90mdc [0m[90mdd [0m[90mde [0m[90mdf [0m
[90me0 [0m[90me1 [0m[90me2 [0m[90me3 [0m[90me4 [0m[90me5 [0m[90me6 [0m[90me7 [0m[90me8 [0m[90me9 [0m[90mea [0m[90meb [0m[90mec [0m[90med [0m[90mee [0m[90mef [0m
[90mf0 [0m[90mf1 [0m[90mf2 [0m[90mf3 [0m[90mf4 [0m[90mf5 [0m[90mf6 [0m[90mf7 [0m[90mf8 [0m[90mf9 [0m[90mfa [0m[90mfb [0m[90mfc [0m[90mfd [0m[90mfe [0m

'''
        returned_result = addnode.print_existing_things(thing_name='sensor', existing_things=[1, 5])
        self.assertEqual(expected_result, returned_result)

    def test_print_existing_things_handles_empty_lists(self):
        expected_result = 'No existing nodes in database'
        returned_result = addnode.print_existing_things('node', [])
        self.assertEqual(expected_result, returned_result)
        expected_result = 'No existing sensors in database'
        returned_result = addnode.print_existing_things('sensor', [])
        self.assertEqual(expected_result, returned_result)
