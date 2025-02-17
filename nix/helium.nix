{ buildPythonPackage
, python3Packages
, fetchPypi
}:

buildPythonPackage rec {
  pname = "helium";
  version = "5.1.0";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-cpnJJVRlPOpftoakyzc1ZsmCr2yqE/rv2qP8dc89ngY=";
  };

  patches = [
    ./fix_helium_firefox_profile.patch
  ];

  propagatedBuildInputs = with python3Packages; [
    selenium
  ];
}
