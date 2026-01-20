"""Command-line interface with interactive menus"""
import sys
from .config import EXPERIMENTS, MODELS
from .runner import BenchmarkRunner
from .deploy import load_config, deploy_agentcore, start_local_docker, stop_local_docker
from .display import print_error, print_info, print_success, Colors
from .menu import Menu

def main():
    """Main entry point with interactive menus"""
    try:
        # Check if already deployed
        config = load_config()
        has_deployment = 'target' in config
        
        # Main menu
        if has_deployment:
            target_name = "Local Docker" if config['target'] == 'local' else "AgentCore"
            main_options = [
                f"Run Benchmarks (Current: {target_name})",
                "Setup & Deploy",
                "Stop Local Docker" if config['target'] == 'local' else "View Configuration",
                "Exit"
            ]
        else:
            main_options = [
                "Setup & Deploy (Required First)",
                "Exit"
            ]
        
        main_menu = Menu(
            "RLM Benchmark Runner",
            main_options
        )
        
        choice = main_menu.display()
        
        if choice is None or choice == "Exit":
            print(f"\n{Colors.YELLOW}Goodbye!{Colors.END}\n")
            return
        
        # Handle setup & deploy
        if "Setup & Deploy" in choice:
            deploy_options = [
                "Deploy to AgentCore (AWS)",
                "Run Local Docker",
                "Back"
            ]
            
            deploy_menu = Menu(
                "Setup & Deploy",
                deploy_options
            )
            
            deploy_choice = deploy_menu.display()
            
            if deploy_choice == "Deploy to AgentCore (AWS)":
                if deploy_agentcore():
                    print_success("Ready to run benchmarks!")
                    input("\nPress Enter to continue...")
                else:
                    print_error("Deployment failed. Please check errors above.")
                    input("\nPress Enter to continue...")
                return main()  # Return to main menu
                
            elif deploy_choice == "Run Local Docker":
                if start_local_docker():
                    print_success("Ready to run benchmarks!")
                    input("\nPress Enter to continue...")
                else:
                    print_error("Docker start failed. Please check errors above.")
                    input("\nPress Enter to continue...")
                return main()  # Return to main menu
            else:
                return main()  # Back
        
        # Handle stop docker
        if choice == "Stop Local Docker":
            stop_local_docker()
            input("\nPress Enter to continue...")
            return main()
        
        # Handle view config
        if choice == "View Configuration":
            print(f"\n{Colors.CYAN}Current Configuration:{Colors.END}")
            print(f"Target: {config.get('target')}")
            if config.get('target') == 'agentcore':
                print(f"Runtime ARN: {config.get('runtime_arn')}")
            else:
                print(f"Endpoint: {config.get('local_endpoint')}")
            input("\nPress Enter to continue...")
            return main()
        
        # Run benchmarks flow
        if "Run Benchmarks" in choice:
            # Benchmark type menu
            benchmark_options = [
                "Run All Benchmarks",
                "Run Single Experiment",
                "Back"
            ]
            
            benchmark_menu = Menu(
                "Select Benchmark Type",
                benchmark_options
            )
            
            benchmark_choice = benchmark_menu.display()
            
            if benchmark_choice == "Back" or benchmark_choice is None:
                return main()
            
            # Model selection menu
            model_options = list(MODELS.keys())
            model_descriptions = {k: v["description"] for k, v in MODELS.items()}
            
            model_menu = Menu(
                "Select Model Configuration",
                model_options,
                model_descriptions
            )
            
            model_key = model_menu.display()
            
            if model_key is None:
                return main()
            
            # Create runner
            try:
                runner = BenchmarkRunner(model_key=model_key)
            except ValueError as e:
                print_error(str(e))
                input("\nPress Enter to continue...")
                return main()
            
            # Execute based on choice
            if benchmark_choice == "Run All Benchmarks":
                runner.run_all()
                input("\nPress Enter to continue...")
            elif benchmark_choice == "Run Single Experiment":
                # Experiment selection menu
                exp_options = list(EXPERIMENTS.keys())
                exp_descriptions = {k: v["description"] for k, v in EXPERIMENTS.items()}
                
                exp_menu = Menu(
                    "Select Experiment",
                    exp_options,
                    exp_descriptions
                )
                
                experiment = exp_menu.display()
                
                if experiment is None:
                    return main()
                
                runner.run_single(experiment)
                input("\nPress Enter to continue...")
            
            return main()  # Return to main menu
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to continue...")
        return main()

if __name__ == "__main__":
    main()
