
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
if [ ! "x$VENV_CONDA_ID" == "x" ]; then
CONDA_BASE=$(conda info --base); source $CONDA_BASE/etc/profile.d/conda.sh
conda activate $VENV_CONDA_ID
echo "VENV_CONDA_ID=$VENV_CONDA_ID"
fi
fi

if [ "x$VIRTUAL_ENV" == "x" ]; then
source ${VENV_DIR}/bin/activate
fi



