#!/bin/zsh

cd ..
rclone -v sync --no-update-modtime datasource surfdrive:Suriano-Sources-Curated
# rclone -v sync --no-update-modtime curatedscans surfdrive:Suriano-Sources-Scans
