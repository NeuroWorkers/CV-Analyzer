
export PYTHONPATH=$(pwd):$PYTHONPATH

source configs/config.sh.sample
if [ -f configs/config.sh ]; then
source configs/config.sh
fi

./utils/prep_to_cfg.py configs/server_config_sample.py configs/server_config_sample.sh
source configs/server_config_sample.sh
if [ -f configs/server_config.py ]; then
./utils/prep_to_cfg.py configs/server_config.py configs/server_config.sh
source configs/server_config.sh
fi


if [ "x$VIRTUAL_ENV" == "x" ]; then
source ${VENV_DIR}/bin/activate
fi



