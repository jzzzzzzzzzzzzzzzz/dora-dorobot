conda activate dorobot

python operating_platform/core/main.py \
    --robot.type=so101 \
    --record.repo_id=so101-test \
    --record.single_task="start and test so101 arm."

