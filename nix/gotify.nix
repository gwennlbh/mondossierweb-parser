{ buildPythonPackage
, python3Packages
, fetchPypi
, flit-core
}:

buildPythonPackage rec {
  pname = "gotify";
  version = "0.6.0";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-R73AMyFDzVwlHihP+kh0Z0KcYkodQK77ATd09vTdS30=";
  };

  build-system = [
    flit-core
  ];

  propagatedBuildInputs = with python3Packages; [
    httpx
    websockets
  ];
}
