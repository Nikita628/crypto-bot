#!/bin/bash
python -u src/bot/main.py &
python -u src/api/main.py &
wait

