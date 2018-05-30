class Donate(object):

    def __init__(self, var_project):

        if not type(var_project) == self.Project:
            print('your parameters is not correct !')
            return None
        self.var_author = 'AllenCe'
        self.var_project = var_project

    def func_get_author(self):
        return self.author

    def func_donate(self, amount):
        self.project.have += amount
        print('you have donate %s , and the project have %s, we need %s to finish aim ! ' %
              (amount, self.project.have, self.project.aim - self.project.have))

    class Project:
        def __init__(self, name, aim):
            self.name = name
            self.aim = aim
            self.have = 0

        def __repr__(self):
            return '<Project.project>'


if __name__ == '__main__':
    project = Donate.Project('Angel', 100000000)
    d = Donate(project)

