CREATE DATABASE IF NOT EXISTS drawinghall CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE drawinghall;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    foto VARCHAR(255) DEFAULT NULL,
    bio TEXT DEFAULT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE desenhos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT DEFAULT NULL,
    imagem VARCHAR(255) NOT NULL,
    moldura VARCHAR(50) NOT NULL DEFAULT 'classica',
    data_publicacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_desenhos_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE TABLE curtidas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    desenho_id INT NOT NULL,
    UNIQUE KEY uq_curtida (usuario_id, desenho_id),
    CONSTRAINT fk_curtidas_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_curtidas_desenho
        FOREIGN KEY (desenho_id) REFERENCES desenhos(id)
        ON DELETE CASCADE
);

CREATE TABLE seguidores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seguidor_id INT NOT NULL,
    seguido_id INT NOT NULL,
    UNIQUE KEY uq_seguimento (seguidor_id, seguido_id),
    CONSTRAINT fk_seguidores_seguidor
        FOREIGN KEY (seguidor_id) REFERENCES usuarios(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_seguidores_seguido
        FOREIGN KEY (seguido_id) REFERENCES usuarios(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_seguidores_diferentes CHECK (seguidor_id <> seguido_id)
);
