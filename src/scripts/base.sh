export NODE_VERSION=$(if [ -f '.nvmrc' ]; then cat '.nvmrc'; else printf 'default'; fi)
$NVM_DIR/nvm-exec $@
