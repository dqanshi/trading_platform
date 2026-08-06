#!/bin/bash

mkdir -p trading_platform/{config,database/migrations,backend/{schemas,routers},broker,engine,strategy,reports,dashboard/{assets/{css,js,images,fonts},includes},utils,workers,scripts,tests,docs,logs}

touch trading_platform/config/{__init__.py,config.py,logging_config.py}

touch trading_platform/database/{__init__.py,session.py,models.py,repository.py}

touch trading_platform/backend/{__init__.py,main.py,security.py,dependencies.py,middleware.py}
touch trading_platform/backend/schemas/{__init__.py,auth.py,order.py,strategy.py,user.py}
touch trading_platform/backend/routers/{__init__.py,auth.py,orders.py,strategies.py,users.py,websocket.py,admin.py}

touch trading_platform/broker/{__init__.py,kite_client.py,websocket.py,order_manager.py,market_data.py,instruments.py}

touch trading_platform/engine/{__init__.py,trading_engine.py,order_executor.py,risk_manager.py,position_manager.py,portfolio_manager.py,pnl_calculator.py,scheduler.py}

touch trading_platform/strategy/{__init__.py,base_strategy.py,orb_strategy.py,momentum_scanner.py,breakout_strategy.py,mean_reversion.py,indicator_manager.py,strategy_loader.py}

touch trading_platform/reports/{__init__.py,report_generator.py,trade_reports.py,daily_summary.py,performance.py}

touch trading_platform/dashboard/{login.php,logout.php,api.php,index.php,trades.php,positions.php,orders.php,reports.php,settings.php,users.php}
touch trading_platform/dashboard/includes/{auth.php,config.php,database.php}

touch trading_platform/utils/{__init__.py,helpers.py,validators.py,notifier.py,constants.py,exceptions.py}

touch trading_platform/workers/{__init__.py,scheduler.py,market_worker.py,report_worker.py}

touch trading_platform/scripts/{create_admin.py,seed_database.py,migrate.py}

touch trading_platform/tests/{test_api.py,test_engine.py,test_strategy.py,test_broker.py,test_database.py}

touch trading_platform/docs/{API.md,INSTALL.md,DEPLOYMENT.md,ARCHITECTURE.md,STRATEGIES.md}

touch trading_platform/logs/{app.log,trades.log,errors.log,websocket.log}

touch trading_platform/{.env.example,.gitignore,docker-compose.yml,Dockerfile,README.md,requirements.txt,alembic.ini,pyproject.toml,start.py}

echo "Project structure created successfully!"
