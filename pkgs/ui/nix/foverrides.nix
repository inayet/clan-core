{ lib, config, pkgs, ... }:
let

  pjs =
    let
      msg = "foverrides.nix: Expected to find `package.json' to lookup " +
        "package name/version, but no such file exists at: " +
        (toString ../package.json);
    in
    if builtins.pathExists ../package.json then lib.importJSON ../package.json
    else throw msg;
  ident = pjs.name;
  inherit (pjs) version;

  # ---------------------------------------------------------------------------- #

  # example: "13.4.2"
  nextVersion = builtins.head (builtins.attrNames (lib.filterAttrs (name: _attrs: name == "next") config.floco.pdefs).next);

  # we must change the precompiled swc binary depending on the curerent system.
  # example: "@next/swc-linux-x64-gnu"
  swcArch = {
    "x86_64-linux" = "@next/swc-linux-x64-gnu";
    "aarch64-linux" = "@next/swc-linux-arm64-gnu";

    "x86_64-darwin" = "@next/swc-darwin-x64";
    "aarch64-darwin" = "@next/swc-darwin-arm64";
  }.${config.floco.settings.system};

  # '
  #           "@next/swc-darwin-arm64": "13.4.12",
  #         "@next/swc-darwin-x64": "13.4.12",

  #         "@next/swc-linux-arm64-gnu": "13.4.12",
  #         "@next/swc-linux-arm64-musl": "13.4.12",

  #         "@next/swc-linux-x64-gnu": "13.4.12",
  #         "@next/swc-linux-x64-musl": "13.4.12",

in
{

  # ---------------------------------------------------------------------------- #

  config.floco.packages.${ident}.${version} =
    let
      cfg = config.floco.packages.${ident}.${version};
    in
    {

      # ---------------------------------------------------------------------------- #

      # Removes any `*.nix' files as well as `node_modules/' and
      # `package-lock.json' from the source tree before using them in builds.
      source = lib.libfloco.cleanLocalSource ../.;


      # nextjs writes in node_mdules
      built.override.copyTree = true;

      # nextjs chaches some stuff in $HOME
      built.override.preBuild = ''
        export HOME=./home
        ln -s ${pkgs.roboto}/share/fonts ./src/fonts
      '';

      built.tree =
        let
          customOverrides = cfg.trees.dev.overrideAttrs (prev: {
            treeInfo =
              prev.treeInfo
              // {
                "node_modules/${swcArch}" = {
                  key = "${swcArch}/${nextVersion}";
                  link = false;
                  optional = false;
                  dev = true;
                };
              };
          });
        in
        lib.mkForce customOverrides;
    };
}