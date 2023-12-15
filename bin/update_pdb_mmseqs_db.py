#!/usr/bin/env python

import os
import time
import subprocess as sp

SOURCE_URL = "ftp://ftp.wwpdb.org/pub/pdb/derived_data/pdb_seqres.txt"


def get_date():
    year = "%s" % time.localtime().tm_year
    mont = "%02d" % time.localtime().tm_mon
    day = "%02d" % time.localtime().tm_mday
    return "%s%s%s" % (year, mont, day)


def main():
    os.chdir("/feig/s1/huhlim/db/mmseqs/pdb")
    #
    path = get_date()
    if os.path.exists(path):
        print("Exist! (%s)" % path)
        if os.path.exists("current"):
            os.remove("current")
        os.system("ln -sf %s current" % path)
        return
    #
    os.makedirs(path)
    os.chdir(path)
    #
    sp.call(["wget", SOURCE_URL])
    wrt = []
    with open("pdb_seqres.txt") as fp:
        is_protein = False
        for line in fp:
            if line.startswith(">"):
                if "mol:protein" in line:
                    is_protein = True
                else:
                    is_protein = False
            if is_protein:
                wrt.append(line)
    with open("pdb.fasta", "wt") as fout:
        fout.writelines(wrt)
    os.remove("pdb_seqres.txt")

    sp.call(["mmseqs", "createdb", "pdb.fasta", "pdb"])
    sp.call(["mmseqs", "createindex", "pdb", os.getenv("TMPDIR", "/tmp")])

    #
    os.chdir("..")
    if os.path.exists("current"):
        os.remove("current")
    os.system("ln -sf %s current" % path)


if __name__ == "__main__":
    main()
