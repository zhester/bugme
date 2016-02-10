#############################################################################
#
# Makefile
#
# Builds bugme.exe using 64-bit MinGW in a Cygwin environment.
#
#############################################################################

# List of source files
SRCDIR  := src
SOURCES := main.c
RCFILE  := bugme.rc

# Build directory
BLDDIR := build

# Ubiquitous/well-known install prefix
prefix := /usr/local

# Final module image name
IMAGE_NAME := bugme.exe

# Compiler and environment
BINPF   := /usr/bin
CC      := $(BINPF)/i686-w64-mingw32-gcc.exe
CFLAGS  := -Wall -static -mwindows -DWIN32_LEAN_AND_MEAN
LD      := $(CC)
LDFLAGS := -Wall -static -mwindows -s
WR      := $(BINPF)/i686-w64-mingw32-windres.exe
WRFLAGS := -O coff

# Add debug symbols if requested.
debug: CFLAGS += -ggdb
debug: LDFLAGS += -ggdb

# List of intermediate objects
OBJECTS := $(patsubst %.c, $(BLDDIR)/%.o, $(SOURCES))

# Intermediate resource artifact
RESOURCE := $(BLDDIR)/out.res

# Default target
all: $(BLDDIR)/$(IMAGE_NAME)

# Module image target
$(BLDDIR)/$(IMAGE_NAME): $(OBJECTS) $(RESOURCE)
	$(LD) $(LDFLAGS) -o $@ $(OBJECTS) $(RESOURCE) && chmod 700 $@

# Resource information
$(RESOURCE): $(SRCDIR)/$(RCFILE) | $(BLDDIR)
	$(WR) $(WRFLAGS) -o $@ $<

# Intermediate objects
$(BLDDIR)/%.o: $(SRCDIR)/%.c | $(BLDDIR)
	$(CC) $(CFLAGS) -o $@ -c $<

# Build directory
$(BLDDIR):
	mkdir -p $(BLDDIR)

# Install program
install: $(BLDDIR)/$(IMAGE_NAME)
	install -m 0755 $@ $(prefix)/bin

# Clean artifacts
clean:
	rm -rf $(BLDDIR)

# Declare phony targets
.PHONY: all debug install clean

