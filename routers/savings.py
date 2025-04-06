from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import SavingsGoal
from datetime import datetime, timedelta
import json

savings_bp = Blueprint('savings', __name__)

# Dictionary of available Russian folklore characters with their descriptions
FOLKLORE_CHARACTERS = {
    'bogatyr': {
        'name': 'Богатырь (Bogatyr)',
        'description': 'Могучий воин, защитник родной земли. Он поможет вам достичь ваших финансовых целей с отвагой и силой!',
        'image': 'bogatyr.svg'
    },
    'firebird': {
        'name': 'Жар-птица (Firebird)',
        'description': 'Волшебная птица с яркими, сияющими перьями. Она принесет вам удачу и процветание!',
        'image': 'firebird.svg'
    },
    'vasilisa': {
        'name': 'Василиса Прекрасная (Vasilisa)',
        'description': 'Мудрая и красивая героиня, известная своей смекалкой. Она поможет вам разумно распорядиться финансами!',
        'image': 'vasilisa.svg'
    },
    'koschei': {
        'name': 'Кощей (Koschei)',
        'description': 'Хранитель сокровищ, известный своим умением накапливать богатства. Он поможет вам сберечь каждую копейку!',
        'image': 'koschei.svg'
    },
    'domovoi': {
        'name': 'Домовой (Domovoi)',
        'description': 'Хранитель домашнего очага и благополучия. Он присмотрит за вашими финансами и поможет их приумножить!',
        'image': 'domovoi.svg'
    }
}

@savings_bp.route('/savings_goals')
@login_required
def savings_goals():
    """Display all user's savings goals."""
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.created_at.desc()).all()
    
    # Calculate total savings and progress
    total_saved = sum([goal.current_amount for goal in goals])
    total_target = sum([goal.target_amount for goal in goals])
    
    overall_progress = 0
    if total_target > 0:
        overall_progress = (total_saved / total_target) * 100
    
    return render_template(
        'savings_goals.html', 
        goals=goals, 
        characters=FOLKLORE_CHARACTERS, 
        total_saved=total_saved,
        total_target=total_target,
        overall_progress=overall_progress
    )

@savings_bp.route('/savings_goals/new', methods=['GET', 'POST'])
@login_required
def new_savings_goal():
    """Create a new savings goal."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        target_amount = float(request.form.get('target_amount', 0))
        current_amount = float(request.form.get('current_amount', 0))
        character_type = request.form.get('character_type', 'bogatyr')
        
        # Get target date if provided
        target_date_str = request.form.get('target_date')
        target_date = None
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        
        # Validate inputs
        if not title or target_amount <= 0:
            flash('Пожалуйста, введите название и корректную целевую сумму.', 'danger')
            return redirect(url_for('savings.new_savings_goal'))
        
        # Create the new goal
        goal = SavingsGoal(
            user_id=current_user.id,
            title=title,
            description=description,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            character_type=character_type
        )
        
        # Check if achieved
        if current_amount >= target_amount:
            goal.is_achieved = True
        
        db.session.add(goal)
        db.session.commit()
        
        flash('Цель сбережений успешно создана!', 'success')
        return redirect(url_for('savings.savings_goals'))
    
    # GET request - show form
    return render_template('new_savings_goal.html', characters=FOLKLORE_CHARACTERS)

@savings_bp.route('/savings_goals/<int:goal_id>')
@login_required
def view_savings_goal(goal_id):
    """View a specific savings goal."""
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    return render_template('view_savings_goal.html', goal=goal, characters=FOLKLORE_CHARACTERS)

@savings_bp.route('/savings_goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_savings_goal(goal_id):
    """Edit an existing savings goal."""
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        goal.title = request.form.get('title')
        goal.description = request.form.get('description')
        goal.target_amount = float(request.form.get('target_amount', 0))
        goal.current_amount = float(request.form.get('current_amount', 0))
        goal.character_type = request.form.get('character_type', 'bogatyr')
        
        # Update target date
        target_date_str = request.form.get('target_date')
        if target_date_str:
            goal.target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        else:
            goal.target_date = None
        
        # Check if achieved
        if goal.current_amount >= goal.target_amount:
            goal.is_achieved = True
        else:
            goal.is_achieved = False
        
        db.session.commit()
        
        flash('Цель сбережений обновлена!', 'success')
        return redirect(url_for('savings.view_savings_goal', goal_id=goal.id))
    
    # Format date for the form
    target_date = None
    if goal.target_date:
        target_date = goal.target_date.strftime('%Y-%m-%d')
    
    return render_template('edit_savings_goal.html', goal=goal, target_date=target_date, characters=FOLKLORE_CHARACTERS)

@savings_bp.route('/savings_goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_savings_goal(goal_id):
    """Delete a savings goal."""
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(goal)
    db.session.commit()
    
    flash('Цель сбережений удалена!', 'success')
    return redirect(url_for('savings.savings_goals'))

@savings_bp.route('/savings_goals/<int:goal_id>/update_amount', methods=['POST'])
@login_required
def update_amount(goal_id):
    """Update the current amount for a savings goal (AJAX)."""
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    new_amount = float(data.get('amount', goal.current_amount))
    
    # Update the amount
    goal.current_amount = new_amount
    
    # Check if achieved
    if goal.current_amount >= goal.target_amount:
        goal.is_achieved = True
        
    db.session.commit()
    
    # Return updated goal info
    return jsonify({
        'id': goal.id,
        'current_amount': goal.current_amount,
        'target_amount': goal.target_amount,
        'progress': goal.progress_percentage,
        'is_achieved': goal.is_achieved,
        'is_on_track': goal.is_on_track
    })

@savings_bp.route('/savings_goals/celebrate/<int:goal_id>', methods=['POST'])
@login_required
def celebrate_achievement(goal_id):
    """Mark a savings goal as celebrated."""
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    # Here you could add additional logic for celebration
    # For now, we'll just return a success message
    
    return jsonify({
        'success': True,
        'message': 'Поздравляем с достижением цели!',
        'character': FOLKLORE_CHARACTERS.get(goal.character_type, FOLKLORE_CHARACTERS['bogatyr'])
    })