import time
from agent import Agent
from environment import Environment
from random_agent import RandomAgent
from moving_wumpus_environment import MovingWumpusEnvironment
from adaptive_agent import AdaptiveAgent

def get_user_configuration():
    while True:
        try:
            N = int(input("Enter map size N (recommended 4-10, default 8): ") or 8)
            K = int(input(f"Enter number of wumpuses K (recommended 1-{N//2}, default 2): ") or 2)
            p = float(input("Enter pit density (0.0-0.5, recommended 0.1-0.2, default 0.2): ") or 0.2)
            mode = input("Choose mode (1=Intelligent Agent, 2=Random Agent, 3=Compare Agents, 4=Moving Wumpus Mode, default 1): ") or "1"
            break
        except ValueError:
            print("Please enter a valid number.")
    
    return N, K, p, mode

def run_autonomous_mode(env, agent, agent_type="Intelligent"):
    step_count = 0
    max_steps = 300
    print(f"Starting {agent_type.lower()} agent!")

    while step_count < max_steps:
        step_count += 1
        print(f"\n-Step {step_count}")

        print("Real Environment:")
        env.print_map()
        
        percepts = env.env_get_percepts()
        
        agent.Agent_get_percepts(percepts)
        
        print(f"\n{agent_type} Agent's Knowledge:")
        agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y)
        current_score = agent.currentScore()
        print(f"\nCurrent Score: {current_score} | Gold: {'Yes' if agent.has_gold else 'No'}")

        action = agent.choose_action()
        print(f"\n{agent_type} Agent chooses action: {action}")
        
        if action == "FORWARD":
            died, bump = env.move_forward()
            agent.move_forward_action()
            if died:
                agent.die_action()
                print("GAME OVER! Agent died!")
                break
            if bump:
                print("BUMP! Hit a wall!")
        elif action == "LEFT":
            env.turn_left()
            agent.turn_action()
        elif action == "RIGHT":
            env.turn_right()
            agent.turn_action()
        elif action == "SHOOT":
            if agent.shoot_action():
                env.shoot()
                if env.scream:
                    print("SCREAM! Wumpus killed!")
                else:
                    print("Arrow shot, but no scream...")
        elif action == "GRAB":
            if agent.grab_gold_action():
                env.grab_gold()
            else:
                pass
        elif action == "CLIMB":
            if agent.climb_action():
                if env.climb():
                    current_score = agent.currentScore()
                    print(f"FINAL SCORE: {current_score}")
                    break
            else:
                if env.agent_x != 0 or env.agent_y != 0:
                    print("Can only climb at starting position (0,0)!")
        
        # time.sleep(0.5)

    current_score = agent.currentScore()
    print(f"- {agent_type} agent:")
    print(f"+ Total Steps: {step_count}")
    print(f"+ Final Score: {current_score}")
    print(f"+ Gold Retrieved: {'Yes' if agent.has_gold else 'No'}")
    print(f"+ Mission Status: {'SUCCESS' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else 'INCOMPLETE'}")
    print(f"\nScoring:")
    print(f"+ {'Grab Gold: +10 ' if agent.has_gold else 'Grab Gold: +0 '} ")
    print(f"+ {'Shoot Arrow: -10' if agent.shoot else 'Shoot Arrow: -0'}")
    print(f"+ {'Climb Out (with gold): +1000 ' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else 'Climb Out (with gold): -0'}")
    print(f"+ {'Die: -1000 ' if current_score <= -1000 else 'Die: -0'}")
    
    return current_score, step_count, agent.has_gold, (env.agent_x == 0 and env.agent_y == 0)

def run_comparison_experiment(N, K, p, num_trials=10):
    print(f"- Agent comparison:")
    print(f"Config: {N}x{N} map, {K} wumpuses, {p} pit density")
    print(f"Running {num_trials} trials for each agent")
    
    intelligent_results = []
    random_results = []
    
    for trial in range(num_trials):
        print(f"\nTrial {trial + 1}/{num_trials}")
        print("-" * 40)
        
        # Create one environment that both agents will face
        shared_env_config = Environment(N=N, K=K, p=p)
        
        # Count pits and wumpuses for display
        pit_count = sum(1 for y in range(N) for x in range(N) if shared_env_config.grid[y][x].pit)
        wumpus_count = sum(1 for y in range(N) for x in range(N) if shared_env_config.grid[y][x].wumpus)
        print(f"Generated shared environment: {pit_count} pits, {wumpus_count} wumpuses")
        
        print(f"Testing Intelligent Agent...")
        env_intelligent = Environment(N=N, K=K, p=p)
        # Copy the grid state from shared environment
        for y in range(N):
            for x in range(N):
                env_intelligent.grid[y][x].pit = shared_env_config.grid[y][x].pit
                env_intelligent.grid[y][x].wumpus = shared_env_config.grid[y][x].wumpus
                env_intelligent.grid[y][x].gold = shared_env_config.grid[y][x].gold
        
        agent_intelligent = Agent(N, K)
        score_i, steps_i, has_gold_i, climbed_i = run_autonomous_mode(env_intelligent, agent_intelligent, "Intelligent")
        intelligent_results.append({
            'score': score_i,
            'steps': steps_i,
            'has_gold': has_gold_i,
            'success': has_gold_i and climbed_i,
            'survived': score_i > -1000
        })
        
        print(f"\n" + "-" * 40)
        
        print(f"Testing Random Agent on SAME environment...")
        env_random = Environment(N=N, K=K, p=p)
        # Copy the same grid state to random agent environment
        for y in range(N):
            for x in range(N):
                env_random.grid[y][x].pit = shared_env_config.grid[y][x].pit
                env_random.grid[y][x].wumpus = shared_env_config.grid[y][x].wumpus
                env_random.grid[y][x].gold = shared_env_config.grid[y][x].gold
        
        agent_random = RandomAgent(N, K)
        score_r, steps_r, has_gold_r, climbed_r = run_autonomous_mode(env_random, agent_random, "Random")
        random_results.append({
            'score': score_r,
            'steps': steps_r,
            'has_gold': has_gold_r,
            'success': has_gold_r and climbed_r,
            'survived': score_r > -1000
        })
    i_scores = [r['score'] for r in intelligent_results]
    i_steps = [r['steps'] for r in intelligent_results]
    i_success_rate = sum(r['success'] for r in intelligent_results) / num_trials * 100
    i_survival_rate = sum(r['survived'] for r in intelligent_results) / num_trials * 100
    i_gold_rate = sum(r['has_gold'] for r in intelligent_results) / num_trials * 100
    i_avg_score = sum(i_scores)/len(i_scores)
    i_avg_steps = sum(i_steps)/len(i_steps)
    
    r_scores = [r['score'] for r in random_results]
    r_steps = [r['steps'] for r in random_results]
    r_success_rate = sum(r['success'] for r in random_results) / num_trials * 100
    r_survival_rate = sum(r['survived'] for r in random_results) / num_trials * 100
    r_gold_rate = sum(r['has_gold'] for r in random_results) / num_trials * 100
    r_avg_score = sum(r_scores)/len(r_scores)
    r_avg_steps = sum(r_steps)/len(r_steps)
    
    score_improvement = i_avg_score - r_avg_score
    success_improvement = i_success_rate - r_success_rate
    survival_improvement = i_survival_rate - r_survival_rate
    efficiency_ratio = r_avg_steps / i_avg_steps
    
    i_decision_efficiency = (i_success_rate/100 * 0.4) + (i_survival_rate/100 * 0.3) + (min(i_avg_score/1000, 1) * 0.2) + (min(1000/i_avg_steps, 1) * 0.1)
    r_decision_efficiency = (r_success_rate/100 * 0.4) + (r_survival_rate/100 * 0.3) + (min(r_avg_score/1000, 1) * 0.2) + (min(1000/r_avg_steps, 1) * 0.1)
    
    print(f"\n-Intelligent agent:\n+ Average Score: {i_avg_score:.1f}\n+ Best Score: {max(i_scores)}\n+ Worst Score: {min(i_scores)}\n+ Average Steps: {i_avg_steps:.1f}\n+ Success Rate: {i_success_rate:.1f}% (found gold + escaped)\n+ Survival Rate: {i_survival_rate:.1f}% (didn't die)\n+ Gold Finding Rate: {i_gold_rate:.1f}%\n+ Decision Efficiency: {i_decision_efficiency:.3f}")
    
    print(f"\n-Random agent:\n+ Average Score: {r_avg_score:.1f}\n+ Best Score: {max(r_scores)}\n+ Worst Score: {min(r_scores)}\n+ Average Steps: {r_avg_steps:.1f}\n+ Success Rate: {r_success_rate:.1f}% (found gold + escaped)\n+ Survival Rate: {r_survival_rate:.1f}% (didn't die)\n+ Gold Finding Rate: {r_gold_rate:.1f}%\n+ Decision Efficiency: {r_decision_efficiency:.3f}")
    
    print(f"\n- Comparison:\n+ Score Improvement: {score_improvement:+.1f} points\n+ Success Rate Improvement: {success_improvement:+.1f}%\n+ Survival Rate Improvement: {survival_improvement:+.1f}%\n+ Efficiency: Intelligent agent is {efficiency_ratio:.1f}x more efficient\n+ Decision Efficiency Improvement: {i_decision_efficiency - r_decision_efficiency:+.3f}")
    
    print(f"\nDECISION EFFICIENCY FORMULA:")
    print(f"DE = (Success_Rate * 0.4) + (Survival_Rate * 0.3) + (Score_Factor * 0.2) + (Speed_Factor * 0.1)")
    print(f"Where:")
    print(f"+ Success_Rate: Percentage of missions completed successfully (0-1)")
    print(f"+ Survival_Rate: Percentage of games where agent didn't die (0-1)")
    print(f"+ Score_Factor: min(Average_Score/1000, 1) - normalized score performance")
    print(f"+ Speed_Factor: min(1000/Average_Steps, 1) - rewards efficiency")
    
    return intelligent_results, random_results

def run_moving_wumpus_mode(env, agent):
    step_count = 0
    max_steps = 300
    print(f"Starting Adaptive agent in Moving Wumpus mode!")
    print("WARNING: Wumpuses move every 5 actions - previous knowledge may become outdated!")

    while step_count < max_steps:
        step_count += 1
        print(f"\n--- Step {step_count} ---")

        print("Real Environment:")
        env.print_map()
        
        percepts = env.env_get_percepts()
        
        agent.Agent_get_percepts(percepts)
        
        wumpus_moved = agent.handle_wumpus_movement_phase(env.action_count)
        
        print(f"\nAdaptive Agent's Knowledge:")
        agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y)
        

        action = agent.choose_action()
        print(f"\nAdaptive Agent chooses action: {action}")
        
        agent_died = False
        
        if action == "FORWARD":
            died, bump = env.move_forward()
            agent.move_forward_action()
            if died:
                agent.die_action()
                agent_died = True
                if env.check_wumpus_collision():
                    print("GAME OVER! Agent was eaten by a moving Wumpus!")
                else:
                    print("GAME OVER! Agent died!")
                break
            if bump:
                print("BUMP! Hit a wall!")
                
        elif action == "LEFT":
            died = env.turn_left()
            agent.turn_action()
            if died:
                agent.die_action()
                print("GAME OVER! Agent was eaten by a moving Wumpus!")
                break
            print("Turned left")
            
        elif action == "RIGHT":
            died = env.turn_right()
            agent.turn_action()
            if died:
                agent.die_action()
                print("GAME OVER! Agent was eaten by a moving Wumpus!")
                break
            print("Turned right")
            
        elif action == "SHOOT":
            if agent.shoot_action():
                died = env.shoot()
                if died:
                    agent.die_action()
                    print("GAME OVER! Agent was eaten by a moving Wumpus!")
                    break
                if env.scream:
                    print("SCREAM! Wumpus killed!")
                    if hasattr(agent, 'inference_engine'):
                        agent.inference_engine.handle_shoot(env.agent_x, env.agent_y, env.agent_dir)
                else:
                    print("Arrow shot, but no scream...")
                    
        elif action == "GRAB":
            if agent.grab_gold_action():
                env.grab_gold()
                if env.check_wumpus_collision():
                    agent.die_action()
                    print("GAME OVER! Agent was eaten by a moving Wumpus during grab!")
                    break
                    
        elif action == "CLIMB":
            if agent.climb_action():
                if env.climb():
                    current_score = agent.currentScore()
                    print("MISSION COMPLETE! Agent successfully escaped with the gold!")
                    print(f"FINAL SCORE: {current_score}")
                    break
            else:
                if env.agent_x != 0 or env.agent_y != 0:
                    print("Can only climb at starting position (0,0)!")
                    
        if env.action_count % 5 == 0 and hasattr(agent, 'inference_engine'):
            print("Re-running inference after Wumpus movement...")
            agent.inference_engine.logic_inference_forward_chaining()
        
        time.sleep(0.7)

    current_score = agent.currentScore()
    print(f"-Adaptive Agent - Moving Wumpus Mode:")
    print(f"+Total Steps: {step_count}")
    print(f"+Total Actions: {env.action_count}")
    print(f"+Wumpus Movements: {env.action_count // 5}")
    print(f"+Final Score: {current_score}")
    print(f"+Gold Retrieved: {'Yes' if agent.has_gold else 'No'}")
    print(f"+Mission Status: {'SUCCESS' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else 'INCOMPLETE'}")
    
    wumpus_movements = env.action_count // 5
    grab_gold_status = 'Yes' if agent.has_gold else 'No'
    shoot_arrow_status = 'Yes' if agent.shoot else 'No'
    climb_out_status = 'Yes' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else 'No'
    die_status = 'Yes' if current_score <= -1000 else 'No'
    adaptation_status = 'Yes' if current_score > -500 else 'Struggled'
    risk_management = 'Excellent' if not agent_died else 'Failed - killed by moving Wumpus'
    
    print(f"\n- Scoring:\n+ Grab Gold: +10 {grab_gold_status}\n+ Move Forward: -1 per move\n+ Turn Left/Right: -1 per turn\n+ Shoot Arrow: -10 {shoot_arrow_status}\n+ Climb Out (with gold): +1000 {climb_out_status}\n+ Die: -1000 {die_status}")
    
    if wumpus_movements > 0:
        print(f"\nMOVING WUMPUS CHALLENGE ANALYSIS:\n+ Wumpus moved {wumpus_movements} times during the game\n+ Agent adapted to dynamic environment: {adaptation_status}\n+ Risk Management: {risk_management}")
    else:
        print(f"\nMOVING WUMPUS CHALLENGE ANALYSIS:\n+ No Wumpus movements occurred (game ended before 5 actions)")
    
    return 

if __name__ == "__main__":
    N, K, p, mode = get_user_configuration()

    print(f"Map Size: {N}x{N}")
    print(f"Wumpuses: {K}")
    print(f"Pit Density: {p}")

    if mode == '1':
        print(f"Mode: Intelligent Agent")
        env = Environment(N=N, K=K, p=p) 
        agent = Agent(N, K)
        run_autonomous_mode(env, agent, "Intelligent")
    elif mode == '2':
        print(f"Mode: Random Agent Baseline")
        env = Environment(N=N, K=K, p=p) 
        agent = RandomAgent(N, K)
        run_autonomous_mode(env, agent, "Random")
    elif mode == '3':
        print(f"Mode: Agent Comparison Experiment")
        num_trials = int(input("Enter number of trials per agent (default 5): ") or 5)
        run_comparison_experiment(N, K, p, num_trials)
    elif mode == '4':
        print(f"Mode: Moving Wumpus Mode")
        env = MovingWumpusEnvironment(N=N, K=K, p=p)
        agent = AdaptiveAgent(N, K)
        run_moving_wumpus_mode(env, agent)
    else:
        print("Invalid mode selected.")