xterm -hold -e python3 run_exchange_server.py --host 0.0.0.0 --port 9001 --debug --mechanism cda &
xterm -hold -e python3 broker.py &
<<<<<<< HEAD
xterm -hold -e python3 external_clients.py
=======
xterm -hold -e python3 external_clients.py &
>>>>>>> 91583a3036c7f1dbd95defb6ea2b6ac9221e534a
