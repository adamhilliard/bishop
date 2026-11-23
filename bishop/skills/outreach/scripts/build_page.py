# -*- coding: utf-8 -*-
"""Bishop (github.com/adamhilliard/bishop) by Adam Hilliard. MIT license.

Outreach was retired in Bishop 2.1.0. LinkedIn's data export stopped carrying connections' job titles
and companies, which the board needed to sort anyone into a group.

This file stays so that a search set up on 2.0, whose cycle prompt still asks for an outreach rebuild,
doesn't hit a missing file before its weekly check removes that step. It builds nothing, changes
nothing, and always succeeds. The person's existing board still opens as it did.
"""
import sys

print("Outreach was retired in Bishop 2.1.0, so there is no board to rebuild. "
      "Skip this step and leave it out of the digest. The weekly check removes it from the cycle prompt.")
sys.exit(0)
