{
  inputs.nixpkgs.url = "nixpkgs/nixos-unstable";
  inputs.flake-utils.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      with import nixpkgs { inherit system; };
      with pkgs.poetry2nix; rec {
        packages.default =
          (mkPoetryApplication { projectDir = ./.; }).overrideAttrs (old: {
            nativeBuildInputs = old.nativeBuildInputs or [ ]
              ++ [ pkgs.installShellFiles ];
            postInstall = ''
              installShellCompletion --cmd blobber \
                    --bash <(_BLOBBER_COMPLETE=bash_source $out/bin/blobber) \
                    --zsh <(_BLOBBER_COMPLETE=zsh_source $out/bin/blobber) \
            '';
          });
        devShells.default = (mkPoetryEnv { projectDir = ./.; }).env;
      });
}
