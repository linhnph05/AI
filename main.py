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
    max_steps = 200
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
        
        time.sleep(0.5)

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
        
        print(f"Testing Intelligent Agent...")
        env_intelligent = Environment(N=N, K=K, p=p)
        agent_intelligent = Agent(N)
        score_i, steps_i, has_gold_i, climbed_i = run_autonomous_mode(env_intelligent, agent_intelligent, "Intelligent")
        intelligent_results.append({
            'score': score_i,
            'steps': steps_i,
            'has_gold': has_gold_i,
            'success': has_gold_i and climbed_i,
            'survived': score_i > -1000
        })
        
        print(f"\n" + "-" * 40)
        
        print(f"Testing Random Agent...")
        env_random = Environment(N=N, K=K, p=p)
        agent_random = RandomAgent(N)
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
    
    print(f"\n-Intelligent agent:\n+ Average Score: {i_avg_score:.1f}\n+ Best Score: {max(i_scores)}\n+ Worst Score: {min(i_scores)}\n+ Average Steps: {i_avg_steps:.1f}\n+ Success Rate: {i_success_rate:.1f}% (found gold + escaped)\n+ Survival Rate: {i_survival_rate:.1f}% (didn't die)\n+ Gold Finding Rate: {i_gold_rate:.1f}%")
    
    print(f"\n-Random agent:\n+ Average Score: {r_avg_score:.1f}\n+ Best Score: {max(r_scores)}\n+ Worst Score: {min(r_scores)}\n+ Average Steps: {r_avg_steps:.1f}\n+ Success Rate: {r_success_rate:.1f}% (found gold + escaped)\n+ Survival Rate: {r_survival_rate:.1f}% (didn't die)\n+ Gold Finding Rate: {r_gold_rate:.1f}%")
    
    print(f"\n- Comparison:\n+ Score Improvement: {score_improvement:+.1f} points\n+ Success Rate Improvement: {success_improvement:+.1f}%\n+ Survival Rate Improvement: {survival_improvement:+.1f}%\n+ Efficiency: Intelligent agent is {efficiency_ratio:.1f}x more efficient")
    
    return intelligent_results, random_results

def run_moving_wumpus_mode(env, agent, agent_type="Intelligent"):
    step_count = 0
    max_steps = 300
    print(f"Starting {agent_type.lower()} agent in Moving Wumpus mode!")
    print("WARNING: Wumpuses move every 5 actions - previous knowledge may become outdated!")

    while step_count < max_steps:
        step_count += 1
        print(f"\n--- Step {step_count} ---")

        print("Real Environment:")
        env.print_map()
        
        percepts = env.env_get_percepts()
        
        agent.Agent_get_percepts(percepts)
        
        wumpus_moved = agent.handle_wumpus_movement_phase(env.action_count)
        
        print(f"\n{agent_type} Agent's Knowledge:")
        agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y)
        
        current_score = agent.currentScore()
        actions_until_wumpus_move = 5 - (env.action_count % 5)
        print(f"\nScore: {current_score} | Gold: {'Yes' if agent.has_gold else 'No'} | Actions until Wumpus move: {actions_until_wumpus_move}")

        action = agent.choose_action()
        print(f"\n{agent_type} Agent chooses action: {action}")
        
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
    print(f"-{agent_type.upper()} Agent - Moving Wumpus Mode:")
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
    
    return current_score, step_count, agent.has_gold, (env.agent_x == 0 and env.agent_y == 0)

if __name__ == "__main__":
    N, K, p, mode = get_user_configuration()

    print(f"Map Size: {N}x{N}")
    print(f"Wumpuses: {K}")
    print(f"Pit Density: {p}")

    if mode == '1':
        print(f"Mode: Intelligent Agent")
        env = Environment(N=N, K=K, p=p) 
        agent = Agent(N)
        current_score, steps, has_gold, climbed = run_autonomous_mode(env, agent, "Intelligent")
        efficiency_analysis = f"{len(agent.kb.visited)}/{env.N * env.N} cells explored"
        risk_mgmt_analysis = 'Excellent' if current_score > 500 else 'Good' if current_score > 0 else 'Needs Improvement'
        planning_effectiveness = 'Optimal' if agent.has_gold else 'Suboptimal'
        
        print(f"\nIntelligent Agent Performance Analysis:\nEfficiency: {efficiency_analysis}\nRisk Management: {risk_mgmt_analysis}\nPlanning Effectiveness: {planning_effectiveness}")
    elif mode == '2':
        print(f"Mode: Random Agent Baseline")
        env = Environment(N=N, K=K, p=p) 
        agent = RandomAgent(N)
        current_score, steps, has_gold, climbed = run_autonomous_mode(env, agent, "Random")
        efficiency_analysis = f"{len(agent.visited)}/{env.N * env.N} cells explored"
        risk_mgmt_analysis = 'Poor - Random decisions' if current_score < 0 else 'Lucky!'
        
        print(f"\nRandom Agent Performance Analysis:\nEfficiency: {efficiency_analysis}\nRisk Management: {risk_mgmt_analysis}\nPlanning Effectiveness: None - Pure randomness")
    elif mode == '3':
        print(f"Mode: Agent Comparison Experiment")
        num_trials = int(input("Enter number of trials per agent (default 5): ") or 5)
        run_comparison_experiment(N, K, p, num_trials)
    elif mode == '4':
        print(f"Mode: Moving Wumpus Mode")
        agent_choice = input("Choose agent type (1=Adaptive Agent, 2=Standard Agent, default Adaptive): ") or "1"
        
        if agent_choice == '1':
            env = MovingWumpusEnvironment(N=N, K=K, p=p)
            agent = AdaptiveAgent(N)
            current_score, steps, has_gold, climbed = run_moving_wumpus_mode(env, agent, "Adaptive")
            adaptability_status = 'Excellent' if current_score > 0 else 'Good' if current_score > -500 else 'Needs Improvement'
            dynamic_planning = 'Effective' if has_gold else 'Challenged by moving threats'
            survival_status = 'Success' if current_score > -1000 else 'Failed - killed by Wumpus'
            knowledge_mgmt = 'Effective' if len(agent.outdated_wumpus_knowledge) < 5 else 'Struggled with uncertainty'
            
            print(f"\nAdaptive Agent in Moving Wumpus Environment:\n+ Adaptability: {adaptability_status}\n+ Dynamic Planning: {dynamic_planning}\n+ Survival: {survival_status}\n+ Movement Adaptation: {agent.movement_phases} wumpus movement phases handled\n+ Knowledge Management: {knowledge_mgmt}")
        elif agent_choice == '2':
            env = MovingWumpusEnvironment(N=N, K=K, p=p)
            agent = Agent(N)
            current_score, steps, has_gold, climbed = run_moving_wumpus_mode(env, agent, "Standard")
            survival_status = 'Success' if current_score > -1000 else 'Failed - killed by Wumpus'
            
            print(f"\nStandard Agent in Moving Wumpus Environment:\n+ Adaptability: Limited - no dynamic knowledge management\n+ Dynamic Planning: Basic - may struggle with moving threats\n+ Survival: {survival_status}")
        else:
            print("Invalid agent choice.")
    else:
        print("Invalid mode selected.")