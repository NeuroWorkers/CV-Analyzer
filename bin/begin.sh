
export PYTHONPATH=$(pwd):$PYTHONPATH

source configs/config.sh.sample
if [ -f configs/config.sh ]; then
source configs/config.sh
fi

#source configs/server_config_sample.py
#if [ -f configs/server_config.py ]; then
#source configs/server_config.py
#fi


if [ "x$VIRTUAL_ENV" == "x" ]; then
source ${VENV_DIR}/bin/activate
fi



