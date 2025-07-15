drop table if exists authorship;
drop table if exists article;
drop table if exists author;

CREATE TABLE article (
  `pubkey` int NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `mdate` date not null,
  `dblpkey` varchar(255) not null,
  `venue` varchar(32) not null,
  `type` varchar(32) not null,
  `title` varchar(255) not null,
  `year` int not null,
  `pages` varchar(32),
  `volume` varchar(32),
  `number` varchar(255),
  `publisher` varchar(255),
  `isbn` varchar(32),
  `series` varchar(255),
  `booktitle` varchar(255),
  `journal` varchar(255),
  `doi` varchar(1024)) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE author (
  `authorkey` int NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `lastname` varchar(128) NOT NULL,
  `orcid` varchar(32),
  `dblpkey` varchar(255) NOT NULL) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE authorship (
    `pubkey` int NOT NULL,
    `authorkey` int NOT NULL,
    `authornumber` int NOT NULL,
    `publishedasname` varchar(255) NOT NULL,
    FOREIGN KEY (`pubkey`) REFERENCES article(pubkey) ON DELETE CASCADE,
    FOREIGN KEY (`authorkey`) REFERENCES author(authorkey) ON DELETE CASCADE) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

  

