fullpath = fullfile('output', 'Job-1.mat')
field = 'S';  % S, NT11
T = read_mat(fullpath, field);



function T = read_mat(fullpath, field)

mat_data = load(fullpath);

T =  array2table(mat_data.(field).data);
T.Properties.VariableNames = join(string(mat_data.(field).col_index));

T2 = array2table(mat_data.(field).row_index);
T2.Properties.VariableNames = mat_data.(field).row_index_names;

for i = 1:width(T2)
    cur_var = T2.Properties.VariableNames{i};
    T2.(cur_var) = cell2mat(T2.(cur_var));
end

T = [T2, T];
head(T(:, 1:10), 10)
disp(['data has shape ', num2str(size(T))])

end