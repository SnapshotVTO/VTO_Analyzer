def simulate_bidding(crew_data, my_seniority, total_lines):
    available_lines = set(range(1, total_lines + 1))
    assignments = []
    
    # Sort by seniority
    crew_data.sort(key=lambda x: x['seniority'])
    
    my_rank_in_bid = 0
    found_me = False
    
    for index, crew in enumerate(crew_data):
        sen = crew['seniority']
        
        # Stop if we reach the user's seniority
        if sen >= my_seniority:
            # Your rank is the current index + 1
            my_rank_in_bid = index + 1
            found_me = True
            break
            
        assigned = None
        for bid in crew['bids']:
            if bid in available_lines:
                assigned = bid
                available_lines.remove(bid)
                break
        
        status = f"Line {assigned}" if assigned else "No Line Awarded"
        assignments.append({'Seniority': sen, 'Awarded': status})
    
    # If the user is deeper in the list than the file goes (or file is incomplete)
    if not found_me:
        my_rank_in_bid = len(crew_data) + 1

    return sorted(list(available_lines)), assignments, my_rank_in_bid
