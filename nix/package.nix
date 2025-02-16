{ buildPythonPackage
, python3Packages
, poetry-core
, firefox
, xorg
}:

buildPythonPackage {
  pname = "mondossierweb";
  version = "0.1.2";
  pyproject = true;

  src = ../.;

  build-system = [
    poetry-core
  ];

  dependencies = [
    firefox
    xorg.xorgserver
  ];

  propagatedBuildInputs = with python3Packages; [
    docopt
    beautifulsoup4
    helium
    lxml
    pyvirtualdisplay
    gotify
    requests
  ];
}
