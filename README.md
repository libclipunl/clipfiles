clipfiles
=========

###[Instalador para Windows](http://nng.is-a-geek.net/clipfiles/win/clipfiles.exe)

Um programa para descarregar documentos do CLIP.
Este programa foi concebido para todos os alunos da FCT/UNL que dependem do CLIP para aceder a
documentos importantes, nomeadamente testes e exames de anos anteriores tal como acetatos, entre outros
tipos de documentos.

Com este programa pode ser-se específico na escolha de documentos que se pretenda descarregar, com menos
cliques e com maior rapidez possível. Ou então, descarregar em massa todos os ficheiros, de alguma
unidade curricular ou ano.

Como utilizar
-------------

Após introduzir o seu identificador CLIP e palavra-passe, poderá escolher que documentos deseja guardar
no seu computador.

Pode escolher vários anos e/ou unidades curriculares, em vez de descarregar tudo.
Para escolher mais que um item, basta manter a tecla Ctrl pressionada e clicar nos itens desejados.

(Clique [aqui](http://windows.microsoft.com/pt-pt/windows-vista/select-multiple-files-or-folders) se tem
dificuldade em selecionar mais que um item.)

Por fim, clique no botão _Download_, escolha onde quer guardar os seus documentos, e as transferências
iniciar-se-ão. Note que na pasta escolhida será criada uma nova pasta de nome **CLIP**, e é aqui que
encontrará todos os seus ficheiros.

Erros e melhorias
-----------------

Este programa tem muito por onde melhorar. É um programa recente e em desenvolvimento.
Qualquer erro ou sugestão contacte-me via e-mail: david.nonamedguy@gmail.com

Se tiver conta no _GitHub_ sugiro que relate erros, apresente sugestões para melhorias, correcções
ou até mesmo perguntas de utilização na
[página de _issues_ deste projecto](https://github.com/libclipunl/clipfiles/issues).

Se desejar (e tiver as capacidades necessárias para) ajudar no código, _design_ ou noutro
aspecto relevante no desenvolvimento deste projecto, contacte-me. É essa a magia do _open-source_.
Ou então faça um _fork_ deste projecto.

Instalação
----------

###Windows

O instalador mais recente para Windows está disponível em:

http://nng.is-a-geek.net/clipfiles/win/clipfiles.exe

Clique no link acima, siga as instruções que lhe aparecem no ecrã, e desfruta do programa.

###Linux

Pacotes de instalação disponíveis em breve. Por enquanto, poderá instalar a partir da fonte.

###Mac

Em teoria este programa é capaz de correr em sistemas Mac. Porém, ainda não tive a possibilidade
de pôr essa teoria à prova, visto que não disponho de um Mac. Se algum proprietário de Mac dispuser
de algum do seu tempo (tal como o seu Mac), instruções e instaladores poderão ser feitos.

###A partir da fonte

O **clipfiles** foi desenvolvido em **Python 2.7**. Se tiver o **Python 2.7** no seu sistema, basta
seguir as instruções abaixo descritas.

Este projecto depende do [pyclipunl](https://www.github.com/libclipunl/pyclipunl), por isso será necessário
ir à página desse projecto, e verificar as suas dependências. A grande dependência externa do
**pyclipunl** é o [BeautifulSoup 4](http://www.crummy.com/software/BeautifulSoup/).

Se não estiver interessado em instalar o **pyclipunl** para o _site-packages_ do seu sistema, basta
copiar o ficheiro [ClipUNL.py](https://github.com/libclipunl/pyclipunl/blob/master/ClipUNL.py)
para o mesmo directório onde se encontre o código-fonte do **clipfiles**.

Este metódo de instalação é recomendado apenas a utilizadores avançados, ou desenvolvedores interessados
em modificar ou melhorar o **clipfiles**.

Screenshots
-----------
**CLIPFiles** a correr no Windows 7:
![clipfiles downloading and working on Windows](http://i.imgur.com/vkPlIvG.png "Windows Version")
