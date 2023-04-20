TAR= main

.PHONY: all clean

CC = g++ -g -I/usr/include/mysql -L/usr/lib64/mysql -L .  -Wl,-rpath=. -lmysqlclient -lpthread -ldl -lz -lssl -lcrypto -lresolv -lm -lrt
VERSION = -std=c++11
CFLAG = -c $(VERSION) 


INC_PATH = ./include/
OBJ_PATH = ./objs/
SOURCE=$(wildcard *.cpp)
OBJ=$(patsubst %.cpp,$(OBJ_PATH)%.o,$(SOURCE))

HEADER = $(wildcard $(INC_PATH)*.h)


all:$(TAR)
	

$(TAR):$(OBJ)
	$(CC) -Wall $(VERSION) -I$(INC_PATH) -o $@  $^


$(OBJ):$(OBJ_PATH)%.o:%.cpp $(HEADER)
	$(CC) $(CFLAG) -I$(INC_PATH) -o $@ $<

clean:
	rm -f $(TAR) $(OBJ)