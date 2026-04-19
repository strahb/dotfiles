# --- Pre-Config (Path deduplication) ---
    typeset -U path PATH
    # Path array
    path=(
        $HOME/bin
        /usr/local/bin
        $HOME/.local/bin
        $HOME/.cargo/bin
        $path
    )
    export PATH

# --- History Configuration ---
    HISTFILE=~/.histfile
    HISTSIZE=5000
    SAVEHIST=5000
    setopt APPEND_HISTORY      # Save history from multiple terminals
    setopt SHARE_HISTORY       # Share history across open terminals
    setopt HIST_IGNORE_DUPS    # Don't record same command twice

# --- Plugin Management (Antidote static) ---
    source ${ZDOTDIR:-$HOME}/.antidote/antidote.zsh
    # Static loading is significantly faster than 'antidote load'
    static_plugin_file=${ZDOTDIR:-$HOME}/.zsh_plugins.zsh
    if [[ ! -f "$static_plugin_file" || ${ZDOTDIR:-$HOME}/.zsh_plugins.txt -nt "$static_plugin_file" ]]; then
    antidote bundle < ${ZDOTDIR:-$HOME}/.zsh_plugins.txt > "$static_plugin_file"
    fi
    source "$static_plugin_file"

# --- Shell Options & Completion ---
    bindkey -e # Use Emacs mode (standard for word-jumping)
    export ZSH_AUTOSUGGEST_STRATEGY=(history completion)

    # Extra file alias Exports
    export DOTS=$HOME/dotfiles
    export NIRI=$DOTS/niri


    # Case-insensitive completion & menu selection
    zstyle ':completion:*' menu select
    zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 

    # Initialize completions
    autoload -Uz compinit
    # Only regenerate the completion dump file once a day
    if [[ -n ${ZDOTDIR:-$HOME}/.zcompdump(#qN.m-1) ]]; then
    compinit -C
    else
    compinit
    fi

# --- Aliases ---
    # eza aliases
    alias ls='eza -F --icons --group-directories-first'
    alias la='eza -a -F --icons --group-directories-first'
    alias tree='eza -a -F -T --icons'
    
    # General aliases
    alias cat='bat'
    alias ..='cd ..'
    alias ...='cd .. && cd ..'
    alias .='pwd'
    alias fetch='fastfetch'
    alias end='cd ~'
    alias aria='aria2c'
    alias dots='cd $DOTS'
    alias calc='numbat -e'

# --- Tool Initializations ---
    [[ -f ~/.zoxide.zsh ]] && source ~/.zoxide.zsh
    [[ -f ~/.starship.zsh ]] && source ~/.starship.zsh

# --- Keybindings ---
    # Jump entire words (CTRL + ArrowKey)
    bindkey "^[[1;5D" backward-word
    bindkey "^[[1;5C" forward-word

    # Delete entire words (CTRL + BackSpace)
    bindkey '^H' backward-kill-word
    bindkey '^[[3;5~' kill-word