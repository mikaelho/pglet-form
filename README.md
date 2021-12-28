# pglet-form

Data-model-driven validated forms for Pglet.

Get a quick start by [viewing a demo](https://pglet-form.mikaelho.repl.co/) ("manual") of the Form control on replit.

# Easy web development for Python developers

Web technologies are available everywhere, and they seem like a good way to create a graphical user interface for
your Python application, either on the desktop or on the web. Unfortunately, most Python coders like Python,
and would like to avoid using a lot of other languages (HTML, Javascript and CSS) just to get a UI created.

Pglet ("pagelet") is a server using React components and providing a protocol for clients to control the UI. One
of the available languages is Python. The server comes nicely bundled in the install, so all you need is:

`pip install pglet`

and you are off to creating a web-enabled UI in pure Python (3.7+).

For supported controls and a tutorial, see the [pglet Python docs](https://pglet.io/docs/).

# Easy forms

One of the most-repeated type of UI is some kind of form for entering and updating information. While creating
forms is easy in pglet, it is nevertheless a task that provides little programming joy. The Form control eats 
annotated Python classes, for example, Python's [dataclasses](https://docs.python.org/3/library/dataclasses.html),
and creates the form to enter corresponding data.

Form control supports all main data types, lists of data and nested data structures.

# Easy forms with validation

Typically you also need to somehow validate user input before you can use it for anything: check that
necessary values have been provided, check that numbers are numbers, check dates etc.

You can avoid this repetitive code by giving the Form control a [pydantic](https://pydantic-docs.helpmanual.io/)
object. Validation defined on the object is performed before the data is returned to you. In some cases,
you can use the exact same data definition with your APIs (e.g. FastAPI) or when writing to a document or SQL
data store.
