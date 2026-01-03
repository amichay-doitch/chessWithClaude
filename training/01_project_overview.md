# Chess ML Engine - Overview Document
# מנוע שחמט מבוסס למידה - מסמך סקירה

---

## English Version

### Project Goal
Build two chess engines based on machine learning that can:
1. **Select the next move** (policy/move selection)
2. **Evaluate positions** (value/position evaluation)

### Data
- Starting with ~1000 games
- Will generate more data as needed

### Approach: Reinforcement Learning
The engines will learn through reinforcement learning - improving by playing and learning from outcomes.

### Two Models

#### Model 1: Classical ML (Simple)
- **No neural networks**
- Classical machine learning techniques (e.g., decision trees, linear models, gradient boosting)
- Faster to train and iterate
- Easier to interpret and debug
- Will serve as baseline and proof of concept

#### Model 2: Neural Network
- Deep learning approach
- More complex architecture
- Higher potential performance ceiling
- Will be developed after Model 1 is working

### Development Order
1. First: Classical ML model (simpler, faster iteration)
2. Second: Neural network model (more complex, potentially stronger)

### Deliverables
- End-to-end design document (Hebrew + English)
- Working engines integrated into existing engine pool
- Training pipeline
- Evaluation framework

---

## גרסה בעברית

### מטרת הפרויקט
לבנות שני מנועי שחמט מבוססי למידת מכונה שיכולים:
1. **לבחור את המהלך הבא** (policy/בחירת מהלך)
2. **להעריך פוזיציות** (value/הערכת מצב)

### נתונים
- מתחילים עם ~1000 משחקים
- נייצר עוד נתונים לפי הצורך

### גישה: למידת חיזוק (Reinforcement Learning)
המנועים ילמדו דרך למידת חיזוק - ישתפרו על ידי משחק ולמידה מתוצאות.

### שני מודלים

#### מודל 1: למידת מכונה קלאסית (פשוט)
- **ללא רשתות נוירונים**
- טכניקות למידת מכונה קלאסיות (למשל: עצי החלטה, מודלים לינאריים, gradient boosting)
- מהיר יותר לאימון ואיטרציה
- קל יותר להבנה ודיבוג
- ישמש כבסיס והוכחת היתכנות

#### מודל 2: רשת נוירונים
- גישת deep learning
- ארכיטקטורה מורכבת יותר
- פוטנציאל ביצועים גבוה יותר
- יפותח אחרי שמודל 1 עובד

### סדר פיתוח
1. ראשון: מודל למידת מכונה קלאסית (פשוט יותר, איטרציה מהירה)
2. שני: מודל רשת נוירונים (מורכב יותר, פוטנציאל חזק יותר)

### תוצרים
- מסמך דיזיין מקצה לקצה (עברית + אנגלית)
- מנועים עובדים משולבים ב-engine pool הקיים
- צינור אימון (training pipeline)
- מסגרת הערכה (evaluation framework)

---

## Next Step / השלב הבא
Design document for Model 1 (Classical ML) - מסמך דיזיין למודל 1 (למידה קלאסית)
