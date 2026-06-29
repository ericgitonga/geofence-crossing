#!/bin/bash

# Derive generated directory from spec.yaml id field
WORKFLOW_ID=$(grep '^id:' spec.yaml | sed 's/^id: *//' | tr '_' '-')
GENERATED_DIR="ecoscope-workflows-${WORKFLOW_ID}-workflow"

echo "recompiling spec.yaml"

/home/gitonga/.pixi/envs/wt-compiler/bin/wt-compiler compile --spec=spec.yaml "$@"
