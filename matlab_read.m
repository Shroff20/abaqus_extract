
%  change this to your python.exe path, make sure the package pandas is installed
pyenv(Version="C:\Users\ssmee\.conda\envs\py310\python.exe")

pe = pyenv;
pe.Status % should say loaded

try
    py.importlib.import_module('pandas');
    disp('Pandas loaded successfully!')
catch
    disp('Pandas still not found. Try: pip install pandas')
end

try
    py.importlib.import_module('pytables');
    disp('Pandas loaded successfully!')
catch
    disp('Pandas still not found. Try: pip install pandas')
end