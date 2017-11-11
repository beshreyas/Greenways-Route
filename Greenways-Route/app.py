import MySQLdb
import scipy as sp
from scipy.sparse.csgraph import dijkstra
from flask import Flask, json, render_template, request, redirect, session, flash
from flaskext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash
from pandas import *

mysql=MySQL()
app = Flask(__name__)
app.secret_key = '1227'


app.config['MYSQL_DATABASE_USER'] = 'shreyas'
app.config['MYSQL_DATABASE_PASSWORD'] = 'admin'
app.config['MYSQL_DATABASE_DB'] = 'login1'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


connection = MySQLdb.connect (host = "localhost", user = "shreyas", passwd = "admin", db = "login1")


@app.route("/")
def main():
    return render_template('index.html')


@app.route("/showSignUp")
def showSignUp():
    return render_template('signup.html')

@app.route('/signUp',methods=['POST'])
def signUp():
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        if _name and _email and _password:
            
            conn = mysql.connect()
            cursor = conn.cursor()
            _hashed_password = generate_password_hash(_password)
            cursor.callproc('sp_createUser',(_name,_email,_hashed_password))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return json.dumps({'message':'User created successfully!'})
            else:
                return json.dumps({'error':str(data[0])})

        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error':str(e)})

    finally:
        cursor.close()
        conn.close()

@app.route('/showSignin')
def showSignin():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('signin.html')

@app.route('/showSuccess')
def showSuccess():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('showSuccess.html')



@app.route('/displayAQI')
def displayAQI():
    aqi=0
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.callproc('sp_dispaqi',(aqi,))
    data = cursor.fetchall()

    if len(data) is 0:
        return json.dumps({'error':str(data[0])})
    else:
        return data[0][0]


@app.route('/viewAQI')
def viewAQI():
    if session.get('user'):
        dv_aqi = displayAQI()
        return render_template('viewAQI.html',variable = dv_aqi)
    else:
        return render_template('error.html',error = 'Unauthorized Access')


@app.route('/selectSD')
def selectSD():
    if session.get('user'):
        return render_template('selectSD.html')
    else:
        return render_template('error.html',error='Unauthorized Access')


@app.route('/upTree')
def upTree():
    if session.get('user'):
        return render_template('upTree.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')


@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html',error = 'Unauthorized access')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

@app.route('/forestHome')
def forestHome():
    if session.get('user'):
        return render_template('forestHome.html')
    else:
        return render_template('error.html',error= 'Unauthorized access')

@app.route('/pcbHome')
def pcbHome():
    if session.get('user'):
        dp_aqi = displayAQI()
        return render_template('pcbHome.html',variable=dp_aqi)
    else:
        return render_template('error.html',error= 'Unauthorized Access')


@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']


        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin',(_username,))
        data = cursor.fetchall()

        if len(data) > 0:
            if check_password_hash(str (data[0][3]),_password):
                session['user']=data[0][0]
                if data[0][2] == "forestdept@smail.com":
                    return redirect('/forestHome')
                elif data[0][2]=="pcb123@smail.com":
                    return redirect('/pcbHome')
                else:
                    return redirect('/userHome')
            else:
                return render_template('error.html',error = 'Wrong Email address or Password.')
        else:
            return render_template('error.html',error = 'iWrong Email address or Password.')


    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        con.close()




@app.route('/updateAQI',methods=['POST'])
def updateAQI():
    try:
        _aqi = request.form['inputaqi']

        if _aqi:
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_upaqi',(_aqi,))
            data = cursor.fetchall()
            cursor.execute('update connect_info set weight=poll_level+road_length')
            if len(data) is 0:
                conn.commit()
                return json.dumps({'message':'Updated Successfully!'})
            else:
                return json.dumps({'error':str(data[0])})

        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error':str(e)})

    finally:
        cursor.close()
        conn.close()



@app.route('/updateTreeIndex',methods=['POST'])
def updateTreeIndex():
    try:
        _point1 = request.form['node1']
        _point2 = request.form['node2']
        _treeIn = request.form['inputTree']

        if _point1 and _point2 and _treeIn:
            con = mysql.connect()
            cursor1 = con.cursor()
            cursor1.callproc('sp_uptree',(_point1,_point2,_treeIn))
            data = cursor1.fetchall()
            cursor1.execute('update connect_info set weight=poll_level+road_length')
            if len(data) is 0:
                con.commit()
                flash('Updated Successfully')
                return render_template('upTree.html')
            else:
                return json.dumps({'error':str(data[0])})

        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error':str(e)})

    finally:
        cursor1.close()
        con.close()



def calcpath(_pt1,_pt2,_type):

    cursorx = connection.cursor()
    cursorx.execute("select node1,node2,weight,road_name from connect_info")
    data = cursorx.fetchall()



    mat_data = [ [ 9999 for i in range(41) ] for j in range(41) ]
    q=0
    for row in data :

        i1 = int(row[0])
        j1 = int(row[1])
        k1 = int(row[2])
        '''if q==0:
            print(i1)
            print(j1)
            print(k1)'''
        mat_data[i1-1][i1-1]=0
        '''if q==0:
            print(mat_data[0][0])'''
        mat_data[j1-1][j1-1]=0
        '''if q==0:
            print(i1)
            print(j1)'''
        mat_data[i1-1][j1-1]=k1
        '''if q==1:
            print(mat_data[0][0])'''
        mat_data[j1-1][i1-1]=k1
        #print(mat_data[0][0])
        q=q+1
        '''if q==1:
            print("Iteration %d",q)
            print(DataFrame(mat_data))'''


    print (DataFrame(mat_data))
    pnt1 = int(_pt1)
    pnt2 = int(_pt2)

    distances,pred=dijkstra(mat_data,indices=pnt1-1,return_predecessors=True)

    print("The distance matrix")
    print(DataFrame(distances))
    print("The predec matrix")
    print(DataFrame(pred))
    path = []

    i=pnt2-1

    if distances[i] == 9999:
        print('the path does not exist!')
    else:
        while i!=pnt1-1:
            path.append(i)
            i = pred[i]
        path.append(pnt1-1)
        path = path[::-1]
        path = [x+1 for x in path]
        l=len(path)
        path1=[]
        for x in range(0,l-1):
            select_stmt = "SELECT road_name FROM connect_info WHERE (node1 = %s and node2 = %s) or (node2=%s and node1=%s)"
            dat2 = (path[x],path[x+1],path[x],path[x+1])
            cursorx.execute(select_stmt,dat2)
            dat1=cursorx.fetchall()
            path1.append(dat1[0][0])
    print(path)
    print(path1)
    cursorx.close()
    return path,path1

@app.route('/showRoute',methods=['POST'])
def showRoute():
    try:
        _pt1 = request.form['point1']
        _pt2 = request.form['point2']
        _type = request.form['vehi_type']

        paths,path = calcpath(_pt1,_pt2,_type)
        print(paths)
        print(path)
        return render_template("showRoute.html",paths=paths,pt1=_pt1,pt2=_pt2,type=_type,paths1=path)

    except Exception as e:
        return json.dumps({'error':str(e)})





@app.route('/finishTrip',methods=['POST'])
def finishTrip():
    try:
        _pt1 = request.form['point1']
        _pt2 = request.form['point2']
        _type = request.form['vehi_type']
        type = str(_type)
        paths,path = calcpath(_pt1,_pt2,_type)
        print(paths)
        print(path)
        cursorx = connection.cursor()
        l = len(paths)
        for x in range(0,l-1):
            if type == 'cars':
                statement = "update connect_info set cars=cars+1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            elif type == 'bikes':
                statement = "update connect_info set bikes=bikes+1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            elif type == 'heavy':
                statement = "update connect_info set heavy=heavy+1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            else:
                statement = "update connect_info set others=others + 1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            cursorx.execute("update connect_info set poll_level = 50 + aqi_perc + (cars*0.5) + (bikes*0.75) + (heavy*1) + (others*0.75) - (green_index/10)")
            connection.commit()
            cursorx.execute("update connect_info set weight = poll_level + road_length")
            connection.commit()
        cursorx.close()
        return render_template("finishTrip.html",paths=paths,pt1=_pt1,pt2=_pt2,type=_type,paths1=path)

    except Exception as e:
        return json.dumps({'error':str(e)})







@app.route('/completeTrip',methods=['POST'])
def completeTrip():
    try:
        _pt1 = request.form['point1']
        _pt2 = request.form['point2']
        _type = request.form['vehi_type']
        type = str(_type)
        paths,path = calcpath(_pt1,_pt2,_type)
        print(paths)
        print(path)
        cursorx = connection.cursor()
        l = len(paths)
        for x in range(0,l-1):
            if type == 'cars':
                statement = "update connect_info set cars=cars-1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            elif type == 'bikes':
                statement = "update connect_info set bikes=bikes-1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            elif type == 'heavy':
                statement = "update connect_info set heavy=heavy-1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            else:
                statement = "update connect_info set others=others - 1 where node1 = %s and node2 = %s"
                dat2 = (paths[x],paths[x+1])
                cursorx.execute(statement,dat2)
                connection.commit()
            cursorx.execute("select heavy from connect_info where node1 = 2 and node2 = 5")
            data1=cursorx.fetchall()
            print(data1[0][0])
            cursorx.execute("update connect_info set poll_level = 50 + aqi_perc + (cars*0.5) + (bikes*0.75) + (heavy*1) + (others*0.75) - (green_index/10)")
            connection.commit()
            cursorx.execute("update connect_info set weight = poll_level + road_length")
            connection.commit()
        cursorx.close()
        return render_template("completeTrip.html",paths=paths,pt1=_pt1,pt2=_pt2,type=_type,paths1=path)

    except Exception as e:
        return json.dumps({'error':str(e)})

@app.route('/viewMap')
def viewMap():
    if session.get('user'):
        return render_template('viewMap.html')
    else:
        return render_template('error.html',error= 'Unauthorized access')

if __name__ == "__main__":
    app.run(port=5002)


