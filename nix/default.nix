{ pkgs ? import <nixpkgs> { overlays = [ (import ./overlay.nix) ]; } }:
pkgs.python3Packages.callPackage ./package.nix { }
