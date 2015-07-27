
create table if not exists users(
	useremail varchar(40),
	checked numeric(1,0),
	pw varchar(20),
	nick varchar(20),
	birth numeric(4,0),
	sex varchar(6),
	userdate date,
	primary key(useremail) 
);

create table if not exists checkcode(
	code varchar(20),
	primary key(code)
);

create table if not exists wallpaper(
	wallidx integer primary key,
	useremail varchar(40),
	wcontent tinytext,
	wlike int,
	wdate datetime,
	wtime int(11),
	foreign key(useremail) references users(useremail) 
		on delete cascade
		on update cascade
);
create table if not exists wallcomment(
	commentidx integer primary key,
	wallidx integer,
	useremail varchar(40),
	ccontent tinytext,
	clike int,
	cdate datetime,
	ctime int(11),
	foreign key(wallidx) references wallpaper(wallidx)
		on delete cascade
		on update cascade,
	foreign key(useremail) references users(useremail)
		on delete cascade
		on update cascade
);

create table if not exists commentcomment(
	ccommentidx integer primary key,
	wallidx integer,
	commentidx integer,
	useremail varchar(40),
	cccontent tinytext,
	cclike int,
	ccdate date,
	cctime int(11),
	foreign key(wallidx) references wallpaper(wallidx)
		on delete cascade
		on update cascade,
	foreign key(commentidx) references wallcomment(commentidx)
		on delete cascade
		on update cascade,
	foreign key(useremail) references users(useremail)
		on delete cascade
		on update cascade
);

create table if not exists userlikeWP(
	wallidx integer,
	useremail varchar(40),
	primary key (wallidx, useremail),
	foreign key (wallidx) references wallpaper(wallidx)
		on delete cascade
		on update cascade,
	foreign key (useremail) references users(useremail)
		on delete cascade
		on update cascade
);

create table if not exists userlikeWC(
	commentidx integer,
	useremail varchar(40),
	primary key (commentidx, useremail),
	foreign key (commentidx) references wallcomment(commentidx)
		on delete cascade
		on update cascade,
	foreign key (useremail) references users(useremail)
		on delete cascade
		on update cascade
);

create table if not exists userlikeCC(
	ccommentidx integer,
	useremail varchar(40),
	primary key (ccommentidx, useremail),
	foreign key (ccommentidx) references commentcomment(ccommentidx)
		on delete cascade
		on update cascade,
	foreign key (useremail) references users(useremail)
		on delete cascade
		on update cascade
);


