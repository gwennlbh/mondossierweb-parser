{
  outputs = { self, nixpkgs }:
    let
      # System types to support.
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      # Nixpkgs instantiated for supported system types.
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; overlays = [ (import ./nix/overlay.nix) ]; });
    in
    {
      # enable nix fmt
      formatter = forAllSystems (system:
        nixpkgs.legacyPackages.x86_64-linux.nixpkgs-fmt
      );

      packages = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
        in
        {
          default = pkgs.python3Packages.callPackage ./nix/package.nix {};
        }
      );
    };
}
