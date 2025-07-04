
export PYTHONPATH=$(pwd):$PYTHONPATH

if [ -f configs/config.sh ]; then
source configs/config.sh
else
source configs/config.sh.sample
fi

if [ "x$VIRTUAL_ENV" == "x" ]; then
source ${VENV_DIR}/bin/activate
fi



