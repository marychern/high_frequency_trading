xterm -hold -e python run_exchange_server.py --host 0.0.0.0 --port 9001 --debug --mechanism cda &
xterm -hold -e python test_broker.py &
xterm -hold -e python test_trader_client.py &
xterm -hold -e python random_trader_client.py &
xterm -hold -e "echo Hello My World"

