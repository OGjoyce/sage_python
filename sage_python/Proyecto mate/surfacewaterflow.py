print "Ingrese su funcion en terminos de x=u, y=v ; \n Ingrese un punto inicial y un final para realizar una trayectoria"
var ('x y')
var ('u v')
var('t')
var('punto_inicial')
var('razon')
var('k')
r=vector( ( cos(t),sin(t) ) )
@interact
def _(f = input_box(default=sqrt(64-u^2-v^2)), punto_final = input_box(default=vector((0,0))), punto_inicial=input_box(default=vector((2,2)))):
    f_gradient = f.gradient()
    vector = punto_final - punto_inicial
    vector_unitario = (1/sqrt(vector[0]*vector[0]+vector[1]*vector[1]))*vector
    derx(u,v) = derivative(f(u,v),u)
    dery(u,v) = derivative(f(u,v),v)
    #testing
    solution = solve([derx==0, dery==0], [u,v])
    x_solution = solution[0][0].right_hand_side()
    y_solution = solution[0][1].right_hand_side()
    print x_solution
    print y_solution
    #endoftest
    nablafp = (derx(punto_inicial[0],punto_inicial[1]),dery(punto_inicial[0],punto_inicial[1]))
    nablafp_unitario = (nablafp[0]*vector_unitario[0] + nablafp[1]*vector_unitario[1])
    razon = nablafp_unitario
    print vector_unitario
    print razon
    show(f_gradient)
    show(animate(point((0,0),size=10, figsize=10)+contour_plot(f, (u,-5,5), (v, -5, 5), labels=true, contours=20)+plot_vector_field(f.gradient(), (u,-5,5), (v,-5,5), color='red')+implicit_plot((x-punto_inicial[0]+derx(m,m))^2+(y-punto_inicial[1]+dery(m,m))^2 ==1/18,(x,-5,5),(y,-5,5), fill=true)+arrow2d((f_gradient[0](0,0), f_gradient[1](0,0)),punto_inicial ) for m in srange(0,5,0.25)))