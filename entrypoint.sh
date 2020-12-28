#!/usr/bin/env bash

# This script converts the input from the Github action to the Docker container
# that runs urlsup. It's necessary because the action and the docker file
# systems have the workspace files in different places so a translation layer
# is required.

## Example
#
# Input file path
#   /home/runner/work/urlsup/urlsup/README.md
#
# Which is converted into
#   /github/workspace/README.md
#
# Which is where the repo files are located for Docker to access.

set -e  # Abort on error
set -x  # Print bash commands

readonly input_args=$1
readonly docker_workspace=$GITHUB_WORKSPACE

# Parse repo name, e.g. "simeg/urlsup" => "urlsup"
readonly repo_name=$(echo "$GITHUB_REPOSITORY" | cut -d "/" -f 2)

# Construct action workspace path to be replaced
readonly action_workspace="${RUNNER_WORKSPACE}/${repo_name}"

# Replace action workspace path to docker workspace path
readonly bin_args=${input_args//$action_workspace/$docker_workspace}

urlsup $bin_args  # Don't wrap in double quotes. We want globbing of the variable

