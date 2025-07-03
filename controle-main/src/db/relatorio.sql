USE controle_temp;

SELECT Registros.id, Pessoaa.nome, Registros.data_hora, Registros.tipo
FROM Registros INNER JOIN Pessoas ON Registros.pessoa_id = Pessoa.id
WHERE data_hora BETWEEN '2024-12-01' AND '2025-01-01'
ORDER BY Registros.data_hora ASC;
