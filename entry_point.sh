#!/bin/bash
python -u -m debugpy --listen "0.0.0.0:5001" src/bot/main.py &
python -u src/api/main.py &
wait

