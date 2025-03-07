#!/usr/bin/env python
import os, sys, subprocess
import glob
import argparse
import time

# ____________________________________________________________________________________________________________


# ____________________________________________________________________________________________________________
def absoluteFilePaths(directory):
    files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            files.append(os.path.abspath(os.path.join(dirpath, f)))
    return files


# _____________________________________________________________________________________________________________
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        help="output directory ",
        default="/eos/experiment/fcc/ee/simulation/ClicDet/test/",
    )

    parser.add_argument("--njobs", help="max number of jobs", default=2)

    parser.add_argument(
        "--queue",
        help="queue for condor",
        choices=[
            "espresso",
            "microcentury",
            "longlunch",
            "workday",
            "tomorrow",
            "testmatch",
            "nextweek",
        ],
        default="longlunch",
    )

    args = parser.parse_args()

    outdir = os.path.abspath(args.outdir)

    njobs = int(args.njobs)
    queue = args.queue
    homedir = os.path.abspath(os.getcwd()) + "/../"

    os.system("mkdir -p {}".format(outdir))

    # find list of already produced files:
    list_of_outfiles = []
    for name in glob.glob("{}/*.root".format(outdir)):
        list_of_outfiles.append(name)

    script = "run_sequence_global_Z.sh"

    jobCount = 0

    cmdfile = """# here goes your shell script
executable    = {}

# here you specify where to put .log, .out and .err files
output                = std/condor.$(ClusterId).$(ProcId).out
error                 = std/condor.$(ClusterId).$(ProcId).err
log                   = std/condor.$(ClusterId).log

+AccountingGroup = "group_u_CMST3.all"
+JobFlavour    = "{}"
""".format(
        script, queue
    )

    print(njobs)
    for job in range(njobs):
        if job>13000:
            seed = str(job + 1)
            basename = "reco_Zcard_tau_CLD_" + seed + "_mc2.root"
            outputFile = outdir + "/" + basename

            # print outdir, basename, outputFile
            if not outputFile in list_of_outfiles:
                print("{} : missing output file ".format(outputFile))
                jobCount += 1

                argts = "{}".format(seed)

                cmdfile += 'arguments="{}"\n'.format(argts)
                cmdfile += "queue\n"

                cmd = "rm -rf job*; ./{} {}".format(script, argts)
                if jobCount == 1:
                    print("")
                    print(cmd)

    with open("condor_gun.sub", "w") as f:
        f.write(cmdfile)

    ### submitting jobs
    if jobCount > 0:
        print("")
        print("[Submitting {} jobs] ... ".format(jobCount))
        os.system("condor_submit condor_gun.sub")


# _______________________________________________________________________________________
if __name__ == "__main__":
    main()
