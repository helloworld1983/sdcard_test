#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libserialport.h>
#include <netinet/in.h>

struct sp_port *open_port(char *portname)
{
  struct sp_port *port=NULL;
  struct sp_port_config *com_conf=NULL;
  enum sp_return rc;
  
  if(sp_get_port_by_name(portname, &port))
    {
      fprintf(stderr, "Can't open port\n");
      goto finish;
    }
  
  if(sp_open(port, SP_MODE_READ_WRITE))
    {
      fprintf(stderr, "Can't open port in READ/WRITE mode\n"); 
      goto finish;
    }
  
  sp_new_config(&com_conf);
  sp_set_config_baudrate(com_conf, 115200);
  sp_set_config_parity(com_conf, SP_PARITY_NONE);
  sp_set_config_bits(com_conf, 8);
  sp_set_config_stopbits(com_conf, 1);
  sp_set_config_flowcontrol(com_conf, SP_FLOWCONTROL_NONE);

  if(sp_set_config(port, com_conf))
    {
      fprintf(stderr, "Can't set config \n");
    }

  return port;
  
 finish:
  if(port)
    {
      sp_close(port);
      sp_free_port(port);
      port=NULL;
    }
  if(com_conf)
    {
      sp_free_config(com_conf);
      com_conf=NULL;
    }
  
}


unsigned int read32(struct sp_port *port, unsigned int address)
{
  unsigned char buf[10];
  unsigned int tmp;
  int i;
  
  buf[0] = 2;
  buf[1] = 1;

  sp_blocking_write(port, buf, 2, 5000);
  tmp = htonl(address);
  memcpy(buf, &tmp, 4);
  sp_blocking_write(port, buf, 4, 5000);



  sp_blocking_read(port, (void*)buf, 4, 5000);
  printf("READ: ");
  for(i = 0; i < 4; i++)
    printf("%02x", buf[i]);
  printf("\n");
}

void write32(struct sp_port *port, unsigned int address, unsigned int val)
{
  unsigned char buf[10];
  unsigned int tmp;
  int i;
  
  buf[0] = 1;
  buf[1] = 1;
  
  sp_blocking_write(port, buf, 2, 5000);

  tmp = htonl(address);
  printf("%08x\n", tmp);
  memcpy(buf, &tmp, 4);
  sp_blocking_write(port, buf, 4, 5000);

  tmp = htonl(val);
  printf("%08x\n", tmp);
  memcpy(buf, &tmp, 4);
  sp_blocking_write(port, buf, 4, 5000);


}

int main()
{
  int i;
  struct sp_port *port=NULL;
  port = open_port("/dev/ttyUSB1");
  printf("ok %p\n", port);


  //  write32(port, 0x10000000, 0xdeadbeef);
  //write32(port, 0x10000004, 0xcafebabe);


  for(i = 0; i < 0x100; i+=4)
    read32(port, 0x10000000 + i);

  

}
