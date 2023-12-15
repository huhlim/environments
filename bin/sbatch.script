#!/usr/bin/env python

import os
import sys
import argparse
import subprocess as sp
from tempfile import TemporaryFile

NUM_CPU_PER_NODE = 48
NUM_CPU_PER_GPU = 4
NUM_NODEs = 25
NUM_GPU_PER_NODE = {"default": 8}

TIME_LIMIT = {}
TIME_LIMIT["feig"] = "72:00:00"
TIME_LIMIT["ml"] = "144:00:00"
TIME_LIMIT["openmm"] = "72:00:00"
TIME_LIMIT["all"] = "4:00:00"

PROLOG = """
if [[ -n $SLURM_CPUS_PER_TASK ]]; then
    export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
    export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
    export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
fi
"""

EPILOG = """
n_gpu0=$(grep "NodeName=$HOSTNAME " /etc/slurm.conf | awk '{print $6}' | awk -F: '{print $NF}')
n_gpu=$(nvidia-smi | grep Default | wc -l)
if [[ $n_gpu -lt $n_gpu0 ]]; then
    scontrol update NodeName=$HOSTNAME state=DRAIN reason=reboot
    scontrol requeue $SLURM_JOB_ID
    scontrol requeue $(get_jobid --node $HOSTNAME)
fi
"""


def update_num_gpu_per_node():
    with open("/etc/slurm.conf") as fp:
        for line in fp:
            if not line.startswith("NodeName="):
                continue
            info = {}
            for x in line.strip().split():
                x = x.split("=")
                info[x[0]] = x[1]
            node_name = info.get("NodeName", None)
            if node_name is None:
                raise KeyError(line)
            n_gpu = int(info.get("Gres", "0").split(":")[-1])
            NUM_GPU_PER_NODE[node_name] = n_gpu
    return NUM_GPU_PER_NODE


def write(
    cmd, name=None, partition="feig", conda=None, n_gpu=0, n_cpu=1, output=None, time_limit=None
):
    if time_limit is None:
        time_limit = TIME_LIMIT[partition]
    #
    wrt = []
    wrt.append("#!/bin/bash")
    wrt.append("#")
    wrt.append(f"#SBATCH --partition={partition}")
    # if partition in ['all']:
    #     wrt.append("#SBATCH --exclude=gpu25")
    wrt.append(f"#SBATCH --time={time_limit}")
    wrt.append("#")
    wrt.append(f"#SBATCH --job-name={name}")
    if output is not None:
        wrt.append(f"#SBATCH --output={output}")
    else:
        wrt.append(f"#SBATCH --output=/dev/null")
    wrt.append("#")
    wrt.append(f"#SBATCH --nodes=1")
    wrt.append(f"#SBATCH --cpus-per-task={n_cpu}")
    wrt.append(f"#SBATCH --ntasks-per-node={max(1, n_gpu)}")
    if n_gpu > 0:
        wrt.append(f"#SBATCH --gres=gpu:{n_gpu}")
    wrt.append("#SBATCH --signal=SIGUSR1@90")
    wrt.append("")
    #
    wrt.append(PROLOG)
    #
    if os.getenv("DISPLAY", None) is not None:
        wrt.append("unset DISPLAY")
    #
    if conda is not None:
        wrt.append(f"source activate {conda}")
    wrt.append("\n")
    #
    if isinstance(cmd, list):
        wrt.extend(cmd)
    else:
        wrt.append(cmd)
    #
    if n_gpu > 0:
        wrt.append(EPILOG)
    #
    return "\n".join(wrt)


def main():
    arg = argparse.ArgumentParser(prog="sbatch.script")
    arg.add_argument(
        dest="fp", metavar="FILE", nargs="?", default=sys.stdin, type=argparse.FileType("r")
    )
    arg.add_argument("--name", dest="name", required=True)
    arg.add_argument("--partition", dest="partition", default="feig", choices=["feig", "all", "ml"])
    arg.add_argument("--conda", dest="conda", default=None)
    arg.add_argument("--gpu", dest="n_gpu", default=0, type=int)
    arg.add_argument("--cpu", dest="n_cpu", default=1, type=int)
    arg.add_argument("--output", dest="output", default=None)
    arg.add_argument("--script", dest="script", default=None)
    arg.add_argument("--time", dest="time_limit", default=None)
    arg.add_argument("--hold", dest="hold_job", default=False, action="store_true")
    arg.add_argument("--dependency", dest="dependency", default=[], nargs="*")
    #
    arg = arg.parse_args()
    cmd = []
    for line in arg.fp:
        cmd.append(line.rstrip())
    #
    script = write(
        cmd,
        name=arg.name,
        partition=arg.partition,
        conda=arg.conda,
        n_gpu=arg.n_gpu,
        n_cpu=arg.n_cpu,
        output=arg.output,
        time_limit=arg.time_limit,
    )
    #
    exec = ["sbatch"]
    if arg.hold_job:
        exec.append("--hold")
    if len(arg.dependency) > 0:
        exec.append("--dependency=%s" % (",".join(["afterany:%s" % dep for dep in arg.dependency])))
    #
    if arg.script is not None:
        with open(arg.script, "wt") as fout:
            fout.write(script)
        exec.append(arg.script)
        sp.call(exec)
    else:
        stdin = TemporaryFile(mode="w+t")
        stdin.write(script)
        stdin.flush()
        stdin.seek(0)
        sp.call(exec, stdin=stdin)
        stdin.close()


if __name__ == "__main__":
    main()
