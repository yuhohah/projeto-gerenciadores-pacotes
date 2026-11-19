{
  description = "Exemplo do integrante 3: GNOME Text Editor com Nix";

  # Revisão explícita para que o exemplo não acompanhe uma branch em movimento.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/3ec636362e1816bc2f0888fa0fa2c69f1bc9e504";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forEachSystem = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forEachSystem (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          editor = pkgs.gnome-text-editor;
          default = pkgs.gnome-text-editor;
        });

      devShells = forEachSystem (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShellNoCC {
            packages = [ pkgs.gnome-text-editor ];
          };
        });
    };
}
