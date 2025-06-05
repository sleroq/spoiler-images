{
  description = "Spoiler Images Bot - A Telegram bot that adds spoiler tags to images";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python3Packages;
      in
      {
        packages.default = let
          pythonEnv = pkgs.python3.withPackages (ps: with ps; [
            python-telegram-bot
            anyio
            certifi
            h11
            httpcore
            httpx
            idna
            sniffio
          ]);
        in pkgs.writeScriptBin "spoiler-images-bot" ''
          #!${pythonEnv}/bin/python3
          ${builtins.readFile ./spoilerImagesBot.py}
        '';

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3Packages.pip
            python3Packages.python-telegram-bot
            python3Packages.anyio
            python3Packages.certifi
            python3Packages.h11
            python3Packages.httpcore
            python3Packages.httpx
            python3Packages.idna
            python3Packages.sniffio
          ];
          
          shellHook = ''
            echo "Spoiler Images Bot development environment"
            echo "Python version: $(python3 --version)"
            echo ""
            echo "Available commands:"
            echo "  python3 spoilerImagesBot.py      # Run the bot directly"
            echo "  pip install -r requirements.txt # Install dependencies"
            echo ""
            echo "Required environment variables:"
            echo "  BOT_TOKEN - Your Telegram bot token"
            echo "  CHAT_ID   - Target chat ID (e.g., -1001565619651)"
            echo ""
            echo "Example usage:"
            echo "  export BOT_TOKEN='your_bot_token_here'"
            echo "  export CHAT_ID='-1001565619651'"
            echo "  python3 spoilerImagesBot.py"
          '';
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/spoiler-images-bot";
        };
      });
} 