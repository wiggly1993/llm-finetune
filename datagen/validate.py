from pathlib import Path
import sys
import subprocess
import os
import shutil

from split_reply import split_reply

starting_point = Path(__file__).parent


def run_python_ds_tests(code, d):
    tests = d["tests"]

    solution_path = starting_point / "work" / d["filename"]
    with open(solution_path, "w", encoding="utf-8") as f:
        f.write(code)

    test_solution_path = starting_point / "work" / "test_solution.py"
    with open(test_solution_path, "w", encoding="utf-8") as f:
        f.write(f"from {d["filename"].removesuffix(".py")} import *\n\n")
        f.write(tests)


    result = subprocess.run([sys.executable, "-m", "pytest", "test_solution.py"], 
                        cwd=starting_point / "work" ,capture_output=True, text=True)

    # print("RETURNCODE:", result.returncode)
    # print("STDOUT:", result.stdout) # This will show the SyntaxError

    return result.returncode


def run_js_ds_tests(code, d):
    tests = d["tests"]
    name = d["filename"].removesuffix(".js")

    solution_path = starting_point / "work" / d["filename"]
    with open(solution_path, "w", encoding="utf-8") as f:
        f.write(code)

    header = (
        f"const __exported = require('./{name}');\n"
        "if (typeof __exported === 'function') { globalThis[__exported.name] = __exported; }\n"
        "else { Object.assign(globalThis, __exported); }\n\n"
    )

    test_solution_path = starting_point / "work" / "test_solution.test.js"
    with open(test_solution_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(tests)

    result = subprocess.run(["npx", "jest", "test_solution.test.js"],
                            cwd=starting_point / "work", capture_output=True, text=True)

    # for line in result.stderr.splitlines():
    #     if line.startswith("Tests:"):
    #         print(line)

    # print("RETURNCODE:", result.returncode)
    print("STDERR:", result.stderr)  # jest prints its results to stderr

    return result.returncode


def run_cpp_ds_tests(code, d):
    tests = d["tests"]
    name = d["filename"].removesuffix(".cpp")
    work = starting_point / "work"
    catch_dir = starting_point / "catch2_local"

    with open(work / d["filename"], "w", encoding="utf-8") as f:
        f.write(code)

    header = f'#include "{name}.cpp"\n\n'
    with open(work / "test_solution.cpp", "w", encoding="utf-8") as f:
        f.write(header)
        f.write(tests)

    binary = work / "test_bin"
    if binary.exists():
        binary.unlink()

    compile_result = subprocess.run(
        ["g++", "-std=c++17", "-I", str(catch_dir),
         "test_solution.cpp", str(catch_dir / "catch_amalgamated.o"),
         "-o", "test_bin"],
        cwd=work, capture_output=True, text=True)

    if compile_result.returncode != 0:
        print("COMPILE FAILED:", compile_result.stderr)
        return compile_result.returncode

    try:
        result = subprocess.run(["./test_bin"], cwd=work,
                                capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 1

    print("STDOUT:", result.stdout)  # Catch2 prints to stdout, not stderr
    return result.returncode




def run_rust_ds_tests(code, d):
    tests = d["tests"]
    crate = d["filename"].removesuffix(".rs")
    proj = starting_point / "work" / "rust_proj"
    shutil.rmtree(proj / "tests", ignore_errors=True)
    (proj / "src").mkdir(parents=True, exist_ok=True)

    rust_home = starting_point / "rust_local"
    cargo_bin = rust_home / "cargo" / "bin"
    env = os.environ.copy()
    env["CARGO_HOME"] = str(rust_home / "cargo")
    env["RUSTUP_HOME"] = str(rust_home / "rustup")
    env["PATH"] = str(cargo_bin) + ":" + env["PATH"]

    cargo_toml = (
        "[package]\n"
        f'name = "{crate}"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n\n'
        "[dependencies]\n"
    )
    with open(proj / "Cargo.toml", "w", encoding="utf-8") as f:
        f.write(cargo_toml)

    in_file = f"use {crate}" not in tests

    with open(proj / "src" / "lib.rs", "w", encoding="utf-8") as f:
        f.write(code)
        if in_file:
            f.write("\n\n")
            f.write(tests)

    if not in_file:
        (proj / "tests").mkdir(exist_ok=True)
        with open(proj / "tests" / "ds_tests.rs", "w", encoding="utf-8") as f:
            f.write(tests)

    try:
        result = subprocess.run([str(cargo_bin / "cargo"), "test"], cwd=proj,
                                capture_output=True, text=True, timeout=120,
                                env=env)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 1

    if "could not compile" in result.stderr:
        print("COMPILE FAILED:", result.stderr)
    else:
        print("STDOUT:", result.stdout)

    return result.returncode


def run_go_ds_tests(code, d):
    tests = d["tests"]
    name = d["filename"].removesuffix(".go")
    proj = starting_point / "work" / "go_proj"
    shutil.rmtree(proj, ignore_errors=True)
    proj.mkdir(parents=True)

    go_home = starting_point / "go_local"
    go_bin = go_home / "go" / "bin"
    env = os.environ.copy()
    env["GOROOT"] = str(go_home / "go")
    env["GOPATH"] = str(go_home / "gopath")
    env["GOCACHE"] = str(go_home / "gocache")
    env["GOTOOLCHAIN"] = "local"
    env["GOFLAGS"] = "-mod=mod"
    env["GOPROXY"] = "off"
    env["PATH"] = str(go_bin) + ":" + env["PATH"]

    with open(proj / "go.mod", "w", encoding="utf-8") as f:
        f.write("module dstest\n\ngo 1.24\n")

    with open(proj / d["filename"], "w", encoding="utf-8") as f:
        f.write(code)

    with open(proj / f"{name}_test.go", "w", encoding="utf-8") as f:
        f.write(tests)

    try:
        result = subprocess.run([str(go_bin / "go"), "test", "-vet=off", "./..."],
                                cwd=proj, capture_output=True, text=True,
                                timeout=120, env=env)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 1

    if "[build failed]" in result.stdout or "[setup failed]" in result.stdout:
        print("COMPILE FAILED:", result.stdout, result.stderr)
    else:
        print("STDOUT:", result.stdout)  # go test prints to stdout

    return result.returncode

def run_java_ds_tests(code, d):
    tests = d["tests"]
    name = d["filename"].removesuffix(".java")
    proj = starting_point / "work" / "java_proj"
    shutil.rmtree(proj, ignore_errors=True)
    (proj / "out").mkdir(parents=True)

    jar = starting_point / "junit_local" / "junit-console.jar"

    with open(proj / d["filename"], "w", encoding="utf-8") as f:
        f.write(code)

    with open(proj / f"{name}Test.java", "w", encoding="utf-8") as f:
        f.write(tests)

    try:
        compile_result = subprocess.run(
            ["javac", "-cp", str(jar), "-d", "out",
             d["filename"], f"{name}Test.java"],
            cwd=proj, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 1

    if compile_result.returncode != 0:
        print("COMPILE FAILED:", compile_result.stderr)
        return compile_result.returncode

    try:
        result = subprocess.run(
            ["java", "-jar", str(jar), "execute",
             "--class-path", "out", "--scan-class-path",
             "--disable-banner", "--details=summary"],
            cwd=proj, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 1

    print("STDOUT:", result.stdout)  # JUnit console prints to stdout
    return result.returncode



def tests_validation(d: dict, lang):
    '''
    most important:
    it checks whether the solutions given by ds pass (expect: pass)
    it also checks whether the stubs alone would pass (expect: fail)
    '''
    if lang == "python":
        run_tests = run_python_ds_tests
    elif lang == "javascript":
        run_tests = run_js_ds_tests
    elif lang == "cpp":
        run_tests = run_cpp_ds_tests
    elif lang == "rust":
        run_tests = run_rust_ds_tests
    elif lang == "go":
        run_tests = run_go_ds_tests
    elif lang == "java":
        run_tests = run_java_ds_tests
    else:
        raise ValueError(f"unknown lang: {lang}")

    # solution must pass (expect: 0)
    val_result_sol = run_tests(d["solution"], d)
    info_text_sol = ""
    if val_result_sol != 0:
        info_text_sol = "solution fails tests"

    # stub must fail (expect: not 0)
    val_result_stub = run_tests(d["stub"], d)
    info_text_stub = ""
    if val_result_stub == 0:
        info_text_stub = "stub passes the test which is bad!!"

    if val_result_sol == 0 and val_result_stub != 0:
        return True, ""
    else:
        return False, info_text_sol + " " + info_text_stub


def plan_validation(d: dict):
    '''
    we use this to make sure that the plan is coherent 
    '''
    plan_string = d["plan"]
    if not "```" in plan_string and len(plan_string.split())<=140:  
        return True
    else:
        return False



def build_diff(stub, solution, filename):
    '''
    we constructd our own diff by hand
    input: stub (str), solution (str) and filename (str)
    output: diff (str)
    '''
    diff = "```diff\n"
    diff += f"--- {filename}\n+++ {filename}\n@@ ... @@\n"

    for line in stub.splitlines():
        diff += "-"+line+"\n"

    for line in solution.splitlines():
        diff += "+"+line+"\n"

    diff += "```\n"

    return diff


if __name__ == "__main__":


    full_path_ds_reponse = starting_point / "raw" / "python" /"python_1.txt"
    with open(full_path_ds_reponse, encoding="utf-8") as f:
        raw_ds_output = f.read()
        d = split_reply(text=raw_ds_output)
        #print(d["tests"])

    # print(run_ds_tests(d["stub"], d["tests"]))
    # print(tests_validation(d))
    # print(build_diff(d["stub"], d["solution"], d["filename"]))

    returncode = run_python_ds_tests(d["stub"], d)
    print(returncode)


    #print(starting_point)